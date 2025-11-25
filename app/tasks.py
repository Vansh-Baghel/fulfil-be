# app/tasks.py
import csv
import os
from typing import List, Dict

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from .celery_app import celery_app
from .database import engine
from .models import UploadJob, Product

SessionLocal: sessionmaker[Session] = sessionmaker(bind=engine, autoflush=False, autocommit=False)

BATCH_SIZE = 5000


def _update_upload_status(db: Session, job_id, **fields):
    job = db.get(UploadJob, job_id)
    if job:
        for k, v in fields.items():
            setattr(job, k, v)
        job.updated_at = func.now()
        db.commit()


def _upsert_products_batch(db: Session, batch: List[Dict]):
    # Deduplicate case-insensitive SKUs in the batch
    dedup = {}
    for p in batch:
        key = p["sku"].lower()
        dedup[key] = p  # overwrite previous duplicates

    cleaned_batch = list(dedup.values())

    stmt = insert(Product).values(cleaned_batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=[func.lower(Product.sku)],
        set_={
            "name": stmt.excluded.name,
            "description": stmt.excluded.description,
            "active": stmt.excluded.active,
            "updated_at": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()

@celery_app.task
def import_products(job_id: str, file_path: str):
    db: Session = SessionLocal()
    try:
        job = db.get(UploadJob, job_id)
        if not job:
            return

        job.status = "RUNNING"
        db.commit()

        # First pass: count rows
        total_rows = 0
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for _ in reader:
                total_rows += 1

        job.total_rows = total_rows
        db.commit()

        processed = 0

        # Second pass: import
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch: List[Dict] = []
            for row in reader:
                sku = (row.get("sku") or "").strip()
                if not sku:
                    continue

                product_data = {
                    "sku": sku,
                    "name": (row.get("name") or "").strip() or sku,
                    "description": (row.get("description") or "").strip() or None,
                    "active": True,
                }
                batch.append(product_data)

                if len(batch) >= BATCH_SIZE:
                    _upsert_products_batch(db, batch)
                    processed += len(batch)
                    job.processed_rows = processed
                    db.commit()
                    batch = []

            if batch:
                _upsert_products_batch(db, batch)
                processed += len(batch)
                job.processed_rows = processed
                db.commit()

        job.status = "COMPLETED"
        db.commit()
    except Exception as e:
        db.rollback()
        job = db.get(UploadJob, job_id)
        if job:
            job.status = "FAILED"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)
