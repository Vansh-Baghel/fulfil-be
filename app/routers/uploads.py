# app/routers/uploads.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import os
import shutil

from ..database import get_db
from ..models import UploadJob
from ..schemas import UploadJobOut
from ..tasks import import_products

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/product_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=UploadJobOut)
def create_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = UploadJob(filename=file.filename, status="QUEUED")
    db.add(job)
    db.commit()
    db.refresh(job)

    # async processing
    import_products.delay(str(job.id), dest_path)

    return job


@router.get("/{job_id}", response_model=UploadJobOut)
def get_upload_status(job_id: UUID, db: Session = Depends(get_db)):
    job = db.get(UploadJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    return job
