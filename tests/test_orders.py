from decimal import Decimal


def test_order_total_is_calculated_server_side_and_has_multiple_items(order):
    assert Decimal(order["subtotal"]) == Decimal("491.00")
    assert Decimal(order["discount"]) == Decimal("10.00")
    assert Decimal(order["total"]) == Decimal("481.00")
    assert len(order["items"]) == 2
    assert order["status"] == "confirmed"


def test_historical_price_does_not_change(client, order, products):
    original_price = order["items"][0]["unit_price"]
    response = client.put(
        f"/api/products/{products[0]['id']}", json={"price": "999.99"}
    )
    assert response.status_code == 200

    stored_order = client.get(f"/api/orders/{order['id']}").json()
    assert stored_order["items"][0]["unit_price"] == original_price
    assert Decimal(stored_order["total"]) == Decimal("481.00")


def test_invalid_order_is_atomic(client, customer, products):
    before = client.get("/api/orders").json()["total"]
    response = client.post(
        "/api/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_id": products[0]["id"], "quantity": 2},
                {"product_id": 99999, "quantity": 1},
            ],
        },
    )
    assert response.status_code == 400
    assert client.get("/api/orders").json()["total"] == before


def test_quantity_must_be_positive(client, customer, products):
    response = client.post(
        "/api/orders",
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": products[0]["id"], "quantity": 0}],
        },
    )
    assert response.status_code == 422


def test_completed_order_is_immutable(client, order):
    completed = client.patch(
        f"/api/orders/{order['id']}", json={"status": "completed"}
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    edit = client.patch(f"/api/orders/{order['id']}", json={"notes": "Cambio tardío"})
    assert edit.status_code == 409
    reopen = client.patch(f"/api/orders/{order['id']}", json={"status": "confirmed"})
    assert reopen.status_code == 409


def test_payment_status_progresses_from_partial_to_paid(client, order):
    first = client.post(
        f"/api/orders/{order['id']}/payments",
        json={"amount": "200.00", "method": "Transferencia", "reference": "TEST-PAY-1"},
    )
    assert first.status_code == 201
    assert client.get(f"/api/orders/{order['id']}").json()["payment_status"] == "partial"

    second = client.post(
        f"/api/orders/{order['id']}/payments",
        json={"amount": "281.00", "method": "Efectivo"},
    )
    assert second.status_code == 201
    assert client.get(f"/api/orders/{order['id']}").json()["payment_status"] == "paid"

    excess = client.post(
        f"/api/orders/{order['id']}/payments", json={"amount": "1.00", "method": "Efectivo"}
    )
    assert excess.status_code == 422


def test_order_filters_and_customer_history(client, order, customer):
    filtered = client.get(
        "/api/orders",
        params={"search": "Prueba", "status": "confirmed", "payment_status": "pending"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    history = client.get(f"/api/customers/{customer['id']}/orders")
    assert history.status_code == 200
    assert history.json()["items"][0]["id"] == order["id"]

