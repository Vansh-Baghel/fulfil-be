# app/routers/webhooks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import time
import requests

from ..database import get_db
from ..models import Webhook
from ..schemas import WebhookCreate, WebhookUpdate, WebhookOut, WebhookTestResult

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("/", response_model=list[WebhookOut])
def list_webhooks(db: Session = Depends(get_db)):
    return db.execute(select(Webhook)).scalars().all()


@router.post("/", response_model=WebhookOut)
def create_webhook(data: WebhookCreate, db: Session = Depends(get_db)):
    webhook = Webhook(**data.model_dump())
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.put("/{webhook_id}", response_model=WebhookOut)
def update_webhook(
    webhook_id: int,
    data: WebhookUpdate,
    db: Session = Depends(get_db),
):
    webhook = db.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(webhook, k, v)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    webhook = db.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()
    return {"ok": True}


@router.post("/{webhook_id}/test", response_model=WebhookTestResult)
def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    webhook = db.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    payload = {"event_type": "webhook.test", "data": {"message": "test"}}
    start = time.time()
    try:
        resp = requests.post(webhook.url, json=payload, timeout=5)
        elapsed_ms = (time.time() - start) * 1000
        return WebhookTestResult(
            status_code=resp.status_code,
            elapsed_ms=elapsed_ms,
            ok=resp.ok,
            error=None if resp.ok else resp.text[:200],
        )
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return WebhookTestResult(
            status_code=0,
            elapsed_ms=elapsed_ms,
            ok=False,
            error=str(e),
        )
