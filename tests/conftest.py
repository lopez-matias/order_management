from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def customer(client: TestClient) -> dict:
    response = client.post(
        "/api/customers",
        json={
            "name": "Cliente de Prueba",
            "document": "TEST-CLI-001",
            "email": "cliente@demo.test",
            "phone": "099 000 000",
            "address": "Dirección de prueba",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def products(client: TestClient) -> list[dict]:
    payloads = [
        {"sku": "TEST-A", "name": "Producto A", "price": "125.50", "stock": 30},
        {"sku": "TEST-B", "name": "Producto B", "price": "80.00", "stock": 15},
    ]
    result = []
    for payload in payloads:
        response = client.post("/api/products", json=payload)
        assert response.status_code == 201
        result.append(response.json())
    return result


@pytest.fixture
def order(client: TestClient, customer: dict, products: list[dict]) -> dict:
    response = client.post(
        "/api/orders",
        json={
            "customer_id": customer["id"],
            "order_date": "2026-09-05",
            "due_date": "2026-09-20",
            "discount": "10.00",
            "items": [
                {"product_id": products[0]["id"], "quantity": 2},
                {"product_id": products[1]["id"], "quantity": 3},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()

