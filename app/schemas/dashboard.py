from datetime import date

from pydantic import BaseModel

from app.models import PaymentStatus
from app.schemas.common import Money


class DashboardMetric(BaseModel):
    value: int | Money
    variation: float | None = None


class MonthlySale(BaseModel):
    month: str
    label: str
    total: Money


class TopCustomer(BaseModel):
    id: int
    name: str
    orders_count: int
    total: Money


class TopProduct(BaseModel):
    id: int | None
    name: str
    sku: str
    quantity: int
    total: Money


class RecentOrder(BaseModel):
    id: int
    order_number: str
    customer_name: str
    order_date: date
    status: str
    payment_status: PaymentStatus
    total: Money


class PendingPayment(BaseModel):
    order_id: int
    order_number: str
    customer_name: str
    due_date: date | None
    payment_status: PaymentStatus
    total: Money
    paid: Money
    pending: Money


class DashboardRead(BaseModel):
    sales_this_month: DashboardMetric
    orders_this_month: DashboardMetric
    active_customers: DashboardMetric
    pending_total: DashboardMetric
    monthly_sales: list[MonthlySale]
    top_customers: list[TopCustomer]
    top_products: list[TopProduct]
    recent_orders: list[RecentOrder]
    pending_payments: list[PendingPayment]
