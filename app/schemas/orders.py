from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models import OrderStatus, PaymentRecordStatus, PaymentStatus
from app.schemas.common import Money, ORMModel


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1_000_000)


class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    created_by_id: int | None = Field(default=None, gt=0)
    order_date: date = Field(default_factory=date.today)
    due_date: date | None = None
    discount: Money = Field(default=Decimal("0.00"), ge=Decimal("0"))
    notes: str | None = Field(default=None, max_length=2000)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_order(self) -> "OrderCreate":
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Un producto no puede repetirse; aumente su cantidad")
        if self.due_date and self.due_date < self.order_date:
            raise ValueError("El vencimiento no puede ser anterior a la fecha del pedido")
        return self


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CustomerBrief(ORMModel):
    id: int
    name: str
    document: str


class UserBrief(ORMModel):
    id: int
    full_name: str


class OrderItemRead(ORMModel):
    id: int
    product_id: int | None
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Money
    line_total: Money


class PaymentCreate(BaseModel):
    amount: Money = Field(gt=Decimal("0"))
    method: str = Field(min_length=2, max_length=40)
    reference: str | None = Field(default=None, max_length=100)
    paid_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)


class PaymentRead(ORMModel):
    id: int
    order_id: int
    amount: Money
    method: str
    reference: str | None
    status: PaymentRecordStatus
    paid_at: datetime
    notes: str | None
    created_at: datetime


class OrderRead(ORMModel):
    id: int
    order_number: str
    customer_id: int
    created_by_id: int | None
    status: OrderStatus
    payment_status: PaymentStatus
    order_date: date
    due_date: date | None
    subtotal: Money
    discount: Money
    total: Money
    notes: str | None
    created_at: datetime
    updated_at: datetime
    customer: CustomerBrief
    created_by: UserBrief | None
    items: list[OrderItemRead]
    payments: list[PaymentRead]


class OrderSummary(ORMModel):
    id: int
    order_number: str
    customer_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    order_date: date
    due_date: date | None
    subtotal: Money
    discount: Money
    total: Money
    created_at: datetime
    customer: CustomerBrief


class OrderList(BaseModel):
    items: list[OrderSummary]
    total: int
    page: int
    page_size: int


class UserRead(ORMModel):
    id: int
    full_name: str
    email: str
    role: str
    active: bool

