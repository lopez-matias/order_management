from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentRecordStatus,
    PaymentStatus,
    Product,
    User,
)
from app.schemas.orders import OrderCreate, OrderUpdate, PaymentCreate


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def order_query():
    return select(Order).options(
        selectinload(Order.customer),
        selectinload(Order.created_by),
        selectinload(Order.items),
        selectinload(Order.payments),
    )


def get_order_or_404(db: Session, order_id: int, *, lock: bool = False) -> Order:
    statement = order_query().where(Order.id == order_id)
    if lock:
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


def create_order(db: Session, data: OrderCreate) -> Order:
    customer = db.scalar(
        select(Customer).where(Customer.id == data.customer_id, Customer.active.is_(True))
    )
    if not customer:
        raise HTTPException(status_code=400, detail="El cliente no existe o está inactivo")

    if data.created_by_id:
        user = db.scalar(
            select(User).where(User.id == data.created_by_id, User.active.is_(True))
        )
        if not user:
            raise HTTPException(status_code=400, detail="El usuario no existe o está inactivo")

    product_ids = [item.product_id for item in data.items]
    products = db.scalars(
        select(Product)
        .where(Product.id.in_(product_ids), Product.active.is_(True))
        .with_for_update()
    ).all()
    products_by_id = {product.id: product for product in products}
    missing = sorted(set(product_ids) - products_by_id.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Productos inexistentes o inactivos: {', '.join(map(str, missing))}",
        )

    subtotal = Decimal("0.00")
    line_items: list[OrderItem] = []
    for requested in data.items:
        product = products_by_id[requested.product_id]
        unit_price = money(product.price)
        line_total = money(unit_price * requested.quantity)
        subtotal += line_total
        line_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=requested.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    subtotal = money(subtotal)
    discount = money(data.discount)
    if discount > subtotal:
        raise HTTPException(
            status_code=422, detail="El descuento no puede superar el subtotal"
        )

    order = Order(
        order_number=f"PED-{data.order_date:%Y%m}-{uuid4().hex[:8].upper()}",
        customer_id=data.customer_id,
        created_by_id=data.created_by_id,
        status=OrderStatus.CONFIRMED,
        payment_status=PaymentStatus.PENDING,
        order_date=data.order_date,
        due_date=data.due_date,
        subtotal=subtotal,
        discount=discount,
        total=money(subtotal - discount),
        notes=data.notes,
        items=line_items,
    )
    db.add(order)
    db.flush()
    return get_order_or_404(db, order.id)


ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def update_order(db: Session, order_id: int, data: OrderUpdate) -> Order:
    order = get_order_or_404(db, order_id, lock=True)
    changes = data.model_dump(exclude_unset=True)
    new_status = changes.pop("status", None)

    if new_status and new_status != order.status:
        if new_status not in ALLOWED_TRANSITIONS[order.status]:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede cambiar un pedido {order.status.value} a {new_status.value}",
            )
        order.status = new_status

    if order.status in {OrderStatus.COMPLETED, OrderStatus.CANCELLED} and changes:
        raise HTTPException(
            status_code=409, detail="Los pedidos finalizados conservan su historial y no se editan"
        )
    for field, value in changes.items():
        setattr(order, field, value)
    db.flush()
    return get_order_or_404(db, order.id)


def paid_amount(db: Session, order_id: int) -> Decimal:
    value = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.order_id == order_id,
            Payment.status == PaymentRecordStatus.COMPLETED,
        )
    )
    return money(Decimal(value or 0))


def add_payment(db: Session, order_id: int, data: PaymentCreate) -> Payment:
    order = get_order_or_404(db, order_id, lock=True)
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="No se puede pagar un pedido cancelado")

    already_paid = paid_amount(db, order_id)
    outstanding = money(order.total - already_paid)
    amount = money(data.amount)
    if amount > outstanding:
        raise HTTPException(
            status_code=422,
            detail=f"El pago supera el saldo pendiente de {outstanding}",
        )

    payment = Payment(
        order_id=order.id,
        amount=amount,
        method=data.method.strip(),
        reference=data.reference,
        paid_at=data.paid_at or datetime.now(UTC),
        notes=data.notes,
        status=PaymentRecordStatus.COMPLETED,
    )
    db.add(payment)
    db.flush()
    total_paid = money(already_paid + amount)
    order.payment_status = (
        PaymentStatus.PAID if total_paid >= order.total else PaymentStatus.PARTIAL
    )
    db.flush()
    return payment

