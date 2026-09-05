"""Load deterministic, explicitly fictional data for portfolio demonstrations."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Customer,
    OrderStatus,
    PaymentStatus,
    Product,
    User,
    UserRole,
)
from app.schemas.orders import OrderCreate, OrderItemCreate, PaymentCreate
from app.services.order_service import add_payment, create_order


def demo_hash(value: str) -> str:
    return "demo-sha256$" + hashlib.sha256(value.encode()).hexdigest()


def shifted_month(today: date, offset: int, day: int) -> date:
    absolute = today.year * 12 + today.month - 1 + offset
    year, month = divmod(absolute, 12)
    return date(year, month + 1, min(day, 28))


def seed() -> None:
    with SessionLocal() as db:
        with db.begin():
            if db.scalar(select(User).where(User.email == "admin@demo.test")):
                print("Los datos demostrativos ya existen; no se realizaron cambios.")
                return

            user = User(
                full_name="Admin Demo",
                email="admin@demo.test",
                password_hash=demo_hash("demo-only"),
                role=UserRole.ADMIN,
            )
            db.add(user)
            customers = [
                Customer(name="Cliente Demo Norte", document="DEMO-CLI-001", email="norte@demo.test", phone="099 000 101", address="Zona Norte · Dirección demostrativa"),
                Customer(name="Cliente Demo Centro", document="DEMO-CLI-002", email="centro@demo.test", phone="099 000 202", address="Zona Centro · Dirección demostrativa"),
                Customer(name="Cliente Demo Costa", document="DEMO-CLI-003", email="costa@demo.test", phone="099 000 303", address="Zona Costa · Dirección demostrativa"),
                Customer(name="Cliente Demo Sur", document="DEMO-CLI-004", email="sur@demo.test", phone="099 000 404", address="Zona Sur · Dirección demostrativa"),
                Customer(name="Cliente Demo Oeste", document="DEMO-CLI-005", email="oeste@demo.test", phone="099 000 505", address="Zona Oeste · Dirección demostrativa"),
                Customer(name="Cliente Demo Interior", document="DEMO-CLI-006", email="interior@demo.test", phone="099 000 606", address="Zona Interior · Dirección demostrativa"),
            ]
            products = [
                Product(sku="DEMO-CAF-01", name="Café tostado 1 kg", description="Producto ficticio para demostración", price=Decimal("890.00"), stock=48),
                Product(sku="DEMO-TE-02", name="Té en hebras 500 g", description="Producto ficticio para demostración", price=Decimal("540.00"), stock=32),
                Product(sku="DEMO-AZU-03", name="Azúcar rubia 1 kg", description="Producto ficticio para demostración", price=Decimal("165.50"), stock=120),
                Product(sku="DEMO-CAC-04", name="Cacao en polvo 500 g", description="Producto ficticio para demostración", price=Decimal("475.00"), stock=9),
                Product(sku="DEMO-MIE-05", name="Miel natural 500 g", description="Producto ficticio para demostración", price=Decimal("390.00"), stock=24),
                Product(sku="DEMO-GRA-06", name="Granola artesanal 750 g", description="Producto ficticio para demostración", price=Decimal("425.00"), stock=7),
                Product(sku="DEMO-VAS-07", name="Vasos compostables x50", description="Producto ficticio para demostración", price=Decimal("310.00"), stock=65),
                Product(sku="DEMO-SER-08", name="Servilletas ecológicas x100", description="Producto ficticio para demostración", price=Decimal("185.00"), stock=84),
            ]
            db.add_all(customers + products)
            db.flush()

            today = date.today()
            specs = [
                (-11, 7, 0, [(0, 6), (2, 8)], "paid"),
                (-10, 15, 1, [(1, 8), (6, 5)], "paid"),
                (-9, 9, 2, [(0, 10), (3, 4), (7, 10)], "paid"),
                (-8, 19, 4, [(4, 12), (5, 8)], "paid"),
                (-7, 6, 3, [(2, 20), (6, 10)], "paid"),
                (-6, 21, 0, [(0, 8), (1, 6)], "paid"),
                (-5, 11, 5, [(3, 10), (7, 12)], "partial"),
                (-4, 24, 1, [(0, 12), (4, 8)], "paid"),
                (-3, 5, 2, [(1, 14), (5, 6)], "paid"),
                (-2, 13, 3, [(0, 18), (2, 20), (6, 10)], "partial"),
                (-1, 8, 4, [(3, 7), (4, 9)], "overdue"),
                (-1, 22, 0, [(0, 9), (7, 12)], "paid"),
                (0, 1, 1, [(1, 10), (2, 15)], "paid"),
                (0, 2, 2, [(0, 6), (5, 8)], "partial"),
                (0, 3, 3, [(3, 5), (6, 10)], "pending"),
                (0, 4, 0, [(0, 12), (4, 6), (7, 15)], "paid"),
                (0, 5, 5, [(1, 8), (2, 18)], "pending"),
                (0, 5, 4, [(5, 10), (6, 10)], "pending"),
            ]
            for offset, day, customer_index, item_specs, payment_kind in specs:
                order_date = shifted_month(today, offset, day)
                due_date = order_date + timedelta(days=15)
                order = create_order(
                    db,
                    OrderCreate(
                        customer_id=customers[customer_index].id,
                        created_by_id=user.id,
                        order_date=order_date,
                        due_date=due_date,
                        discount=Decimal("150.00") if len(item_specs) == 3 else Decimal("0.00"),
                        notes="Pedido generado con datos ficticios para la demostración.",
                        items=[OrderItemCreate(product_id=products[p].id, quantity=q) for p, q in item_specs],
                    ),
                )
                order.status = OrderStatus.COMPLETED if order_date < today else OrderStatus.CONFIRMED
                if payment_kind == "paid":
                    add_payment(db, order.id, PaymentCreate(amount=order.total, method="Transferencia", reference=f"DEMO-{order.id:04d}", paid_at=datetime.combine(order_date + timedelta(days=3), datetime.min.time(), tzinfo=UTC)))
                elif payment_kind == "partial":
                    add_payment(db, order.id, PaymentCreate(amount=(order.total / 2).quantize(Decimal("0.01")), method="Tarjeta", reference=f"DEMO-{order.id:04d}", paid_at=datetime.combine(order_date + timedelta(days=2), datetime.min.time(), tzinfo=UTC)))
                elif payment_kind == "overdue":
                    order.payment_status = PaymentStatus.OVERDUE

    print("Datos demostrativos ficticios cargados correctamente.")


if __name__ == "__main__":
    seed()
