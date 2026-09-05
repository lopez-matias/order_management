from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import engine


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    engine.dispose()


settings = get_settings()
openapi_tags = [
    {
        "name": "customers",
        "description": "Create, search, update, deactivate, and inspect customer purchase history.",
    },
    {
        "name": "products",
        "description": "Manage the active product catalog, prices, and inventory visibility.",
    },
    {
        "name": "orders",
        "description": "Create transactional orders, inspect history, transition status, and register payments.",
    },
    {
        "name": "dashboard",
        "description": "Retrieve commercial metrics, monthly trends, rankings, and outstanding balances.",
    },
    {
        "name": "users",
        "description": "List active users that can be assigned as order owners.",
    },
    {
        "name": "system",
        "description": "Application and database health checks.",
    },
]
app = FastAPI(
    title=settings.app_name,
    description=(
        "REST API for managing customers, products, orders, and payments. "
        "Order prices and totals are calculated exclusively by the server, and each "
        "line item preserves a historical product snapshot."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return JSONResponse(status_code=422, content={"detail": "Datos inválidos", "errors": errors})


def render(request: Request, template: str, page: str, title: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"page": page, "title": title, **context},
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "error", "database": "unavailable"}
        )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    return render(request, "dashboard.html", "dashboard", "Panel general")


@app.get("/clientes", response_class=HTMLResponse, include_in_schema=False)
def customers_page(request: Request):
    return render(request, "customers.html", "customers", "Clientes")


@app.get("/productos", response_class=HTMLResponse, include_in_schema=False)
def products_page(request: Request):
    return render(request, "products.html", "products", "Productos")


@app.get("/pedidos", response_class=HTMLResponse, include_in_schema=False)
def orders_page(request: Request):
    return render(request, "orders.html", "orders", "Pedidos")


@app.get("/pedidos/nuevo", response_class=HTMLResponse, include_in_schema=False)
def new_order_page(request: Request):
    return render(request, "order_form.html", "orders", "Nuevo pedido")


@app.get("/pedidos/{order_id}", response_class=HTMLResponse, include_in_schema=False)
def order_detail_page(request: Request, order_id: int):
    return render(
        request, "order_detail.html", "orders", "Detalle del pedido", order_id=order_id
    )
