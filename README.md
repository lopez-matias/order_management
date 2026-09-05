# NODO — Client & Order Management

NODO is a complete web application for managing customers, products, orders, and payments in a small distribution or commercial business. It was built as a portfolio project with production-oriented domain rules, a documented REST API, PostgreSQL persistence, and a responsive interface written without a JavaScript framework or Node.js toolchain.

> Every record loaded by the demo seed is fictional and clearly labeled as demonstration data. The project does not represent real customers, companies, or measured business results.

![NODO dashboard populated with fictional demonstration data](docs/dashboard.png)

The application UI is intentionally written in Spanish to represent a real regional product. Source code, developer documentation, project metadata, and API documentation are written in English.

## Highlights

- Dashboard with monthly sales, order volume, active customers, and outstanding balances.
- Twelve-month sales trend, recent orders, top customers, and top products.
- Customer and product CRUD with search, filtering, pagination, and soft deletion.
- Transactional order creation with multiple line items.
- Partial and full payment registration with outstanding-balance validation.
- Order history and per-customer purchase history.
- Responsive, custom-designed interface for desktop, tablet, and mobile.
- Interactive OpenAPI documentation at `/docs`.
- Deterministic and idempotent fictional demo data.
- Automated tests covering API behavior, business rules, and page rendering.

## Business rules

Order creation and line-item persistence happen in a single database transaction. On PostgreSQL, selected products are locked while their current prices are read, preventing inconsistent concurrent calculations.

The client only submits a product ID and quantity. The server retrieves the current price and calculates every line total, subtotal, discount, and final total. Each `OrderItem` stores a snapshot of the product name, SKU, and unit price, so changing or deactivating a product never modifies historical orders.

Additional safeguards include:

- Quantities must be positive.
- The same product cannot appear twice in one order.
- Discounts cannot exceed the subtotal.
- Payments cannot exceed the outstanding balance.
- Cancelled orders cannot receive payments.
- Completed and cancelled orders cannot be reopened or edited.
- Customers and products are deactivated instead of being physically deleted.

## Technology

- Python 3.12+
- FastAPI and Pydantic 2
- PostgreSQL 17
- SQLAlchemy 2 and Alembic
- Jinja2, HTML, CSS, and vanilla JavaScript
- pytest, HTTPX, and pytest-cov
- Docker and Docker Compose

No Node.js runtime or frontend build step is required.

## Quick start with Docker

Docker Compose is the recommended way to run the complete PostgreSQL-backed application:

```bash
docker compose up --build
```

Once both services are healthy, open:

- Application: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health endpoint: [http://localhost:8000/health](http://localhost:8000/health)

The web container waits for PostgreSQL, applies all Alembic migrations, loads the demo data idempotently, and then starts Uvicorn.

Stop the services without deleting the database volume:

```bash
docker compose down
```

To explicitly remove the local demo database as well:

```bash
docker compose down -v
```

## Local development with PostgreSQL

Create a virtual environment and install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `DATABASE_URL` in `.env` if your PostgreSQL credentials differ, then prepare and run the application:

```bash
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

## Lightweight local preview

SQLite is supported as a convenient preview and isolated test engine. Production and Docker deployments use PostgreSQL.

```bash
source .venv/bin/activate
export DATABASE_URL="sqlite+pysqlite:///./gestion_local.sqlite3"
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

## Configuration

| Variable | Purpose | Example |
|---|---|---|
| `APP_NAME` | Name exposed in the FastAPI schema | `NODO - Commercial Management` |
| `ENVIRONMENT` | Runtime environment label | `development` |
| `DATABASE_URL` | SQLAlchemy database URL | `postgresql+psycopg://gestion:gestion@localhost:5432/gestion_comercial` |
| `SECRET_KEY` | Reserved for authentication and future security extensions | Use a strong secret in production |

Values are loaded from the environment and, when present, from a local `.env` file. The `.env` file is intentionally ignored by Git.

## REST API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET, POST` | `/api/customers` | Search/list customers and create a customer |
| `GET, PUT, DELETE` | `/api/customers/{id}` | Read, update, or deactivate a customer |
| `GET` | `/api/customers/{id}/orders` | Read a customer's purchase history |
| `GET, POST` | `/api/products` | Search/list products and create a product |
| `GET, PUT, DELETE` | `/api/products/{id}` | Read, update, or deactivate a product |
| `GET, POST` | `/api/orders` | Filter order history or create an order |
| `GET, PATCH` | `/api/orders/{id}` | Read an order or transition its status |
| `POST` | `/api/orders/{id}/payments` | Register a payment against an order balance |
| `GET` | `/api/dashboard` | Retrieve dashboard metrics and rankings |
| `GET` | `/api/users` | List active order owners |
| `GET` | `/health` | Check application and database availability |

List endpoints return pagination metadata. Orders can be filtered by free text, order status, payment status, customer, and date range. Customers and products support free-text search and active-state filtering.

See [API documentation](docs/api.md) for request examples, filters, status values, and error behavior.

### Creating an order

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
  "discount": "150.00",
  "notes": "Coordinate delivery during business hours.",
  "items": [
    {"product_id": 1, "quantity": 4},
    {"product_id": 3, "quantity": 2}
  ]
}
```

The contract intentionally accepts neither prices nor totals. Those values are exclusively controlled by the server.

## Tests

Run the complete suite:

```bash
pytest
```

Generate a coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

The suite uses an isolated in-memory SQLite database for each test. It covers CRUD operations, input validation, unique constraints, transactional order creation, server-side totals, historical prices, completed-order immutability, payment progression, filters, dashboard aggregation, OpenAPI exposure, and UI route rendering.

The current suite contains 15 passing tests and reports 94% application-code coverage.

## Project structure

```text
app/
├── api/          # REST endpoints and dependencies
├── core/         # Application configuration
├── db/           # Session management and declarative base
├── models/       # SQLAlchemy entities and enums
├── schemas/      # Pydantic request and response contracts
├── services/     # Order, payment, and dashboard rules
├── static/       # CSS and vanilla JavaScript
└── templates/    # Jinja2 views
alembic/          # Versioned database migrations
docs/             # Architecture, API, and screenshots
scripts/          # Startup and demo-data utilities
tests/            # API, domain, and rendering tests
```

## Design decisions

- **Decimal money values:** monetary calculations use `Decimal` and `NUMERIC(12, 2)` rather than floating-point values.
- **Product snapshots:** order lines preserve their commercial description and price at the time of purchase.
- **Soft deletion:** customer and product history remains available after deactivation.
- **Explicit transaction ownership:** endpoints commit successful service operations and roll back every handled failure.
- **Progressive frontend:** Jinja2 delivers the page structure and vanilla JavaScript consumes the same public API.
- **Safe demo identities:** generic names, `DEMO-*` documents, and addresses under the reserved `.test` domain are used throughout the seed.

Read [Architecture](docs/architecture.md) for the domain model, request flow, transaction boundaries, and reporting strategy.

## Current scope

The `User` entity supports assigning an owner to an order and provides a foundation for future authentication and authorization. To keep this portfolio release focused on commercial operations, it does not include login, tax invoicing, automatic stock deduction, or real payment-provider integrations.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, quality checks, migration guidelines, and pull-request expectations.

## License

No standalone license has been selected. If you plan to allow reuse or redistribution, add an appropriate `LICENSE` file before publication.

