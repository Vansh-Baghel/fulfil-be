# app/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # SKU unique, case-insensitive
        Index("uq_products_sku_lower", func.lower(sku), unique=True),
    )


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="QUEUED")  # QUEUED/RUNNING/COMPLETED/FAILED
    total_rows = Column(Integer, nullable=True)
    processed_rows = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(512), nullable=False)
    event_type = Column(String(50), nullable=False)  # e.g. product.created, product.updated, product.deleted
    enabled = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
