from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import Database
from app.models import Customer, Order, OrderStatus, Payment, PaymentStatus
from app.schemas.orders import (
    OrderCreate,
    OrderList,
    OrderRead,
    OrderSummary,
    OrderUpdate,
    PaymentCreate,
    PaymentRead,
)
from app.services.order_service import add_payment, create_order, get_order_or_404, update_order


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderList)
def list_orders(
    db: Database,
    search: str | None = Query(default=None, max_length=100),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    payment_status: PaymentStatus | None = None,
    customer_id: int | None = Query(default=None, gt=0),
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> OrderList:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Order.order_number.ilike(term), Customer.name.ilike(term)))
    if status_filter:
        filters.append(Order.status == status_filter)
    if payment_status:
        filters.append(Order.payment_status == payment_status)
    if customer_id:
        filters.append(Order.customer_id == customer_id)
    if date_from:
        filters.append(Order.order_date >= date_from)
    if date_to:
        filters.append(Order.order_date <= date_to)

    base = select(Order).join(Customer, Customer.id == Order.customer_id).where(*filters)
    total = db.scalar(
        select(func.count(Order.id))
        .join(Customer, Customer.id == Order.customer_id)
        .where(*filters)
    ) or 0
    orders = db.scalars(
        base.options(selectinload(Order.customer))
        .order_by(Order.order_date.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return OrderList(
        items=[OrderSummary.model_validate(order) for order in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create(data: OrderCreate, db: Database) -> Order:
    try:
        order = create_order(db, data)
        db.commit()
        return get_order_or_404(db, order.id)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible crear el pedido")


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Database) -> Order:
    return get_order_or_404(db, order_id)


@router.patch("/{order_id}", response_model=OrderRead)
def patch_order(order_id: int, data: OrderUpdate, db: Database) -> Order:
    try:
        order = update_order(db, order_id, data)
        db.commit()
        return get_order_or_404(db, order.id)
    except HTTPException:
        db.rollback()
        raise


@router.post(
    "/{order_id}/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED
)
def create_payment(order_id: int, data: PaymentCreate, db: Database) -> Payment:
    try:
        payment = add_payment(db, order_id, data)
        db.commit()
        db.refresh(payment)
        return payment
    except HTTPException:
        db.rollback()
        raise

