# app/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# Product

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int


# Upload job

class UploadJobOut(BaseModel):
    id: UUID
    filename: str
    status: str
    total_rows: Optional[int]
    processed_rows: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Webhooks

class WebhookBase(BaseModel):
    url: HttpUrl
    event_type: str
    enabled: bool = True


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    event_type: Optional[str] = None
    enabled: Optional[bool] = None


class WebhookOut(WebhookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookTestResult(BaseModel):
    status_code: int
    elapsed_ms: float
    ok: bool
    error: Optional[str] = None
