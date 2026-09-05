# REST API

NODO exposes a JSON API under `/api`. Interactive OpenAPI documentation is generated automatically at `/docs`, with the raw schema available at `/openapi.json`.

## Conventions

- Request and response bodies use JSON.
- Monetary values are serialized with two-decimal precision.
- Dates use ISO 8601 `YYYY-MM-DD` format.
- Date-times use ISO 8601 with timezone information.
- Collection endpoints return `items`, `total`, `page`, and `page_size`.
- Validation failures return HTTP `422`.
- Missing resources return HTTP `404`.
- Unique conflicts and invalid state transitions return HTTP `409`.

The UI and API error messages are in Spanish because this release targets a Spanish-language end-user experience. Identifiers, paths, schema names, and developer documentation remain in English.

## Pagination

Customer, product, order, and customer-history collections accept:

| Parameter | Default | Constraints |
|---|---:|---|
| `page` | `1` | Minimum `1` |
| `page_size` | `20` | From `1` to `100` |

Example response envelope:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## Customers

### List customers

```http
GET /api/customers?search=demo&active=true&page=1&page_size=20
```

`search` matches name, document, or email. `active` accepts `true` or `false`; omit it to return both.

### Create a customer

```http
POST /api/customers
Content-Type: application/json
```

```json
{
  "name": "Demo Customer North",
  "document": "DEMO-CUSTOMER-100",
  "email": "north@demo.test",
  "phone": "000 000 100",
  "address": "Fictional demonstration address",
  "notes": null,
  "active": true
}
```

Use `GET /api/customers/{id}`, `PUT /api/customers/{id}`, and `DELETE /api/customers/{id}` for individual records. Delete performs a soft deletion by setting `active` to `false`.

Customer purchase history is available at:

```http
GET /api/customers/{id}/orders
```

## Products

### List products

```http
GET /api/products?search=coffee&active=true&low_stock=false&page=1&page_size=20
```

`search` matches name, SKU, or description. `low_stock=true` limits results to products with ten or fewer units.

### Create a product

```http
POST /api/products
Content-Type: application/json
```

```json
{
  "sku": "DEMO-PRODUCT-100",
  "name": "Fictional demo product",
  "description": "Used only for demonstration",
  "price": "125.50",
  "stock": 30,
  "active": true
}
```

Updating `price` never changes the unit price stored in existing order items. Delete deactivates the product while preserving historical references.

## Orders

### List and filter orders

```http
GET /api/orders?search=PED&status=confirmed&payment_status=pending&date_from=2026-01-01&date_to=2026-12-31
```

Supported filters:

| Parameter | Values |
|---|---|
| `search` | Order number or customer name |
| `status` | `draft`, `confirmed`, `completed`, `cancelled` |
| `payment_status` | `pending`, `partial`, `paid`, `overdue`, `refunded` |
| `customer_id` | Positive customer ID |
| `date_from` | Inclusive start date |
| `date_to` | Inclusive end date |

### Create an order

```http
POST /api/orders
Content-Type: application/json
```

```json
{
  "customer_id": 1,
  "created_by_id": 1,
  "order_date": "2026-09-05",
  "due_date": "2026-09-20",
  "discount": "10.00",
  "notes": "Fictional order for API documentation.",
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 2, "quantity": 3}
  ]
}
```

The server ignores no pricing fields because pricing fields are not accepted at all. It reads current catalog prices and returns the persisted snapshot and calculated totals.

### Transition an order

```http
PATCH /api/orders/{id}
Content-Type: application/json
```

```json
{
  "status": "completed"
}
```

Invalid or terminal-state transitions return HTTP `409`.

## Payments

Register a payment against the current outstanding balance:

```http
POST /api/orders/{id}/payments
Content-Type: application/json
```

```json
{
  "amount": "200.00",
  "method": "Bank transfer",
  "reference": "DEMO-TRANSFER-100",
  "notes": null
}
```

The aggregate order payment status becomes `partial` when the completed payment sum is below the order total and `paid` when it reaches the total. Overpayments are rejected with HTTP `422`.

## Dashboard

```http
GET /api/dashboard
```

The response contains:

- Current-month sales and order metrics.
- Active-customer count.
- Total outstanding balance.
- Twelve monthly sales buckets.
- Top customer and product rankings.
- Recent orders.
- Orders with pending balances.

Cancelled orders are excluded from commercial totals and rankings.

## Health check

```http
GET /health
```

Successful response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

A database connectivity failure returns HTTP `503`.

## Validation error shape

```json
{
  "detail": "Datos inválidos",
  "errors": [
    {
      "field": "items.0.quantity",
      "message": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

The exact message text may vary with the validation rule. API consumers should use the HTTP status and `type` value rather than parsing the human-readable message.
