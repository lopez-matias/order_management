from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import Database
from app.models import Product
from app.schemas.products import ProductCreate, ProductList, ProductRead, ProductUpdate


router = APIRouter(prefix="/products", tags=["products"])


def product_or_404(db: Database, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.get("", response_model=ProductList)
def list_products(
    db: Database,
    search: str | None = Query(default=None, max_length=100),
    active: bool | None = None,
    low_stock: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProductList:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.description.ilike(term),
            )
        )
    if active is not None:
        filters.append(Product.active.is_(active))
    if low_stock:
        filters.append(Product.stock <= 10)
    total = db.scalar(select(func.count(Product.id)).where(*filters)) or 0
    products = db.scalars(
        select(Product)
        .where(*filters)
        .order_by(Product.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ProductList(items=products, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Database) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese SKU")
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Database) -> Product:
    return product_or_404(db, product_id)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate, db: Database) -> Product:
    product = product_or_404(db, product_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese SKU")
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_product(product_id: int, db: Database) -> Response:
    product = product_or_404(db, product_id)
    product.active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

