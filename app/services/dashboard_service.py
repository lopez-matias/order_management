from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentRecordStatus,
    PaymentStatus,
)
from app.schemas.dashboard import (
    DashboardMetric,
    DashboardRead,
    MonthlySale,
    PendingPayment,
    RecentOrder,
    TopCustomer,
    TopProduct,
)
from app.services.order_service import money


MONTH_NAMES = [
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


def month_start(value: date, offset: int = 0) -> date:
    absolute = value.year * 12 + value.month - 1 + offset
    return date(absolute // 12, absolute % 12 + 1, 1)


def variation(current: Decimal | int, previous: Decimal | int) -> float | None:
    if not previous:
        return None
    return round(float((Decimal(current) - Decimal(previous)) / Decimal(previous) * 100), 1)


def get_dashboard(db: Session) -> DashboardRead:
    today = date.today()
    current_start = month_start(today)
    next_start = month_start(today, 1)
    previous_start = month_start(today, -1)
    valid_order = Order.status != OrderStatus.CANCELLED

    current_sales = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                valid_order, Order.order_date >= current_start, Order.order_date < next_start
            )
        )
        or 0
    )
    previous_sales = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                valid_order,
                Order.order_date >= previous_start,
                Order.order_date < current_start,
            )
        )
        or 0
    )
    current_orders = db.scalar(
        select(func.count(Order.id)).where(
            valid_order, Order.order_date >= current_start, Order.order_date < next_start
        )
    ) or 0
    previous_orders = db.scalar(
        select(func.count(Order.id)).where(
            valid_order, Order.order_date >= previous_start, Order.order_date < current_start
        )
    ) or 0
    active_customers = db.scalar(
        select(func.count(Customer.id)).where(Customer.active.is_(True))
    ) or 0

    paid_subquery = (
        select(
            Payment.order_id.label("order_id"),
            func.sum(Payment.amount).label("paid"),
        )
        .where(Payment.status == PaymentRecordStatus.COMPLETED)
        .group_by(Payment.order_id)
        .subquery()
    )
    pending_rows = db.execute(
        select(
            Order.id,
            Order.order_number,
            Customer.name,
            Order.due_date,
            Order.payment_status,
            Order.total,
            func.coalesce(paid_subquery.c.paid, 0),
        )
        .join(Customer, Customer.id == Order.customer_id)
        .outerjoin(paid_subquery, paid_subquery.c.order_id == Order.id)
        .where(
            valid_order,
            Order.payment_status.in_(
                [PaymentStatus.PENDING, PaymentStatus.PARTIAL, PaymentStatus.OVERDUE]
            ),
        )
        .order_by(Order.due_date.asc().nullslast(), Order.order_date.desc())
    ).all()
    pending_payments = [
        PendingPayment(
            order_id=row[0],
            order_number=row[1],
            customer_name=row[2],
            due_date=row[3],
            payment_status=row[4],
            total=money(row[5]),
            paid=money(Decimal(row[6])),
            pending=money(row[5] - Decimal(row[6])),
        )
        for row in pending_rows
    ]

    first_month = month_start(today, -11)
    sales_rows = db.execute(
        select(Order.order_date, Order.total).where(valid_order, Order.order_date >= first_month)
    ).all()
    sales_by_month: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for order_date, total in sales_rows:
        sales_by_month[order_date.strftime("%Y-%m")] += total
    monthly_sales: list[MonthlySale] = []
    for offset in range(-11, 1):
        month = month_start(today, offset)
        key = month.strftime("%Y-%m")
        monthly_sales.append(
            MonthlySale(
                month=key,
                label=f"{MONTH_NAMES[month.month - 1]} {str(month.year)[2:]}",
                total=money(sales_by_month[key]),
            )
        )

    customer_rows = db.execute(
        select(
            Customer.id,
            Customer.name,
            func.count(Order.id),
            func.sum(Order.total),
        )
        .join(Order, Order.customer_id == Customer.id)
        .where(valid_order)
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Order.total).desc())
        .limit(5)
    ).all()
    top_customers = [
        TopCustomer(id=row[0], name=row[1], orders_count=row[2], total=money(row[3]))
        for row in customer_rows
    ]

    product_rows = db.execute(
        select(
            OrderItem.product_id,
            OrderItem.product_name,
            OrderItem.product_sku,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.line_total),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(valid_order)
        .group_by(OrderItem.product_id, OrderItem.product_name, OrderItem.product_sku)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    ).all()
    top_products = [
        TopProduct(id=row[0], name=row[1], sku=row[2], quantity=row[3], total=money(row[4]))
        for row in product_rows
    ]

    recent_rows = db.execute(
        select(
            Order.id,
            Order.order_number,
            Customer.name,
            Order.order_date,
            Order.status,
            Order.payment_status,
            Order.total,
        )
        .join(Customer, Customer.id == Order.customer_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(7)
    ).all()
    recent_orders = [
        RecentOrder(
            id=row[0],
            order_number=row[1],
            customer_name=row[2],
            order_date=row[3],
            status=row[4].value,
            payment_status=row[5],
            total=money(row[6]),
        )
        for row in recent_rows
    ]

    return DashboardRead(
        sales_this_month=DashboardMetric(
            value=money(current_sales), variation=variation(current_sales, previous_sales)
        ),
        orders_this_month=DashboardMetric(
            value=current_orders, variation=variation(current_orders, previous_orders)
        ),
        active_customers=DashboardMetric(value=active_customers),
        pending_total=DashboardMetric(
            value=money(sum((item.pending for item in pending_payments), Decimal("0.00")))
        ),
        monthly_sales=monthly_sales,
        top_customers=top_customers,
        top_products=top_products,
        recent_orders=recent_orders,
        pending_payments=pending_payments[:8],
    )
