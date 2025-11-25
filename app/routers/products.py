# app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from typing import Optional

from ..database import get_db
from ..models import Product
from ..schemas import ProductCreate, ProductUpdate, ProductOut, ProductList

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=ProductList)
def list_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sku: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    active: Optional[bool] = None,
):
    query = select(Product)

    if sku:
        query = query.where(func.lower(Product.sku).like(f"%{sku.lower()}%"))
    if name:
        query = query.where(Product.name.ilike(f"%{name}%"))
    if description:
        query = query.where(Product.description.ilike(f"%{description}%"))
    if active is not None:
        query = query.where(Product.active == active)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.execute(count_stmt).scalar() or 0

    offset = (page - 1) * page_size
    items = db.execute(query.offset(offset).limit(page_size)).scalars().all()

    return ProductList(items=items, total=total, page=page, page_size=page_size)


@router.post("/", response_model=ProductOut)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**product_in.model_dump())
    db.add(product)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"ok": True}


@router.delete("/bulk-delete/all")
def bulk_delete_all(db: Session = Depends(get_db)):
    db.execute(delete(Product))
    db.commit()
    return {"ok": True}
