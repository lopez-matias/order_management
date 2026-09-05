def test_dashboard_aggregates_data(client, order):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert len(data["monthly_sales"]) == 12
    assert data["active_customers"]["value"] == 1
    assert data["recent_orders"][0]["id"] == order["id"]
    assert data["pending_payments"][0]["pending"] == order["total"]


def test_ui_pages_are_available(client):
    for path, text in [
        ("/", "Panel general"),
        ("/clientes", "Clientes"),
        ("/productos", "Productos"),
        ("/pedidos", "Pedidos"),
        ("/pedidos/nuevo", "Crear pedido"),
        ("/pedidos/123", "Cargando detalle"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert text in response.text


def test_openapi_exposes_rest_resources(client):
    schema = client.get("/openapi.json").json()
    assert "/api/customers" in schema["paths"]
    assert "/api/products" in schema["paths"]
    assert "/api/orders" in schema["paths"]
    assert "/api/orders/{order_id}/payments" in schema["paths"]
