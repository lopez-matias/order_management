from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import Database
from app.models import Customer, Order
from app.schemas.customers import (
    CustomerCreate,
    CustomerList,
    CustomerRead,
    CustomerUpdate,
)
from app.schemas.orders import OrderList, OrderSummary


router = APIRouter(prefix="/customers", tags=["customers"])


def customer_or_404(db: Database, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer


@router.get("", response_model=CustomerList)
def list_customers(
    db: Database,
    search: str | None = Query(default=None, max_length=100),
    active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CustomerList:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Customer.name.ilike(term),
                Customer.document.ilike(term),
                Customer.email.ilike(term),
            )
        )
    if active is not None:
        filters.append(Customer.active.is_(active))

    total = db.scalar(select(func.count(Customer.id)).where(*filters)) or 0
    items = db.scalars(
        select(Customer)
        .where(*filters)
        .order_by(Customer.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return CustomerList(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Database) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese documento")
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Database) -> Customer:
    return customer_or_404(db, customer_id)


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, data: CustomerUpdate, db: Database) -> Customer:
    customer = customer_or_404(db, customer_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese documento")
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_customer(customer_id: int, db: Database) -> Response:
    customer = customer_or_404(db, customer_id)
    customer.active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{customer_id}/orders", response_model=OrderList)
def customer_orders(
    customer_id: int,
    db: Database,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> OrderList:
    customer_or_404(db, customer_id)
    total = db.scalar(
        select(func.count(Order.id)).where(Order.customer_id == customer_id)
    ) or 0
    orders = db.scalars(
        select(Order)
        .options(selectinload(Order.customer))
        .where(Order.customer_id == customer_id)
        .order_by(Order.order_date.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return OrderList(
        items=[OrderSummary.model_validate(item) for item in orders],
        total=total,
        page=page,
        page_size=page_size,
    )

