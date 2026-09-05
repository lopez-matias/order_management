from decimal import Decimal


def test_product_crud_filters_and_soft_delete(client):
    response = client.post(
        "/api/products",
        json={"sku": "abc-01", "name": "Producto buscable", "price": "49.90", "stock": 4},
    )
    assert response.status_code == 201
    product = response.json()
    assert product["sku"] == "ABC-01"

    low_stock = client.get("/api/products", params={"low_stock": True, "search": "ABC"})
    assert low_stock.json()["total"] == 1

    updated = client.put(
        f"/api/products/{product['id']}", json={"price": "59.90", "stock": 25}
    )
    assert updated.status_code == 200
    assert Decimal(updated.json()["price"]) == Decimal("59.90")

    assert client.delete(f"/api/products/{product['id']}").status_code == 204
    assert client.get(f"/api/products/{product['id']}").json()["active"] is False


def test_negative_price_and_stock_are_rejected(client):
    response = client.post(
        "/api/products",
        json={"sku": "BAD", "name": "Producto inválido", "price": "-1", "stock": -2},
    )
    assert response.status_code == 422

