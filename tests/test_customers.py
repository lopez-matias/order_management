def test_customer_crud_search_and_soft_delete(client):
    created = client.post(
        "/api/customers",
        json={"name": "Cliente Buscable", "document": "DOC-900", "email": "BUSCAR@DEMO.TEST"},
    )
    assert created.status_code == 201
    customer = created.json()
    assert customer["email"] == "buscar@demo.test"

    result = client.get("/api/customers", params={"search": "Buscable", "active": True})
    assert result.status_code == 200
    assert result.json()["total"] == 1

    updated = client.put(
        f"/api/customers/{customer['id']}",
        json={"name": "Cliente Actualizado", "phone": "123456"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Cliente Actualizado"

    deleted = client.delete(f"/api/customers/{customer['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/customers/{customer['id']}").json()["active"] is False
    assert client.get("/api/customers", params={"active": True}).json()["total"] == 0


def test_customer_document_is_unique(client, customer):
    duplicate = client.post(
        "/api/customers",
        json={"name": "Otro cliente", "document": customer["document"]},
    )
    assert duplicate.status_code == 409


def test_invalid_email_is_rejected(client):
    response = client.post(
        "/api/customers",
        json={"name": "Cliente Inválido", "document": "BAD-1", "email": "correo-invalido"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Datos inválidos"

