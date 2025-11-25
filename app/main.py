# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import uploads, products, webhooks

app = FastAPI(title="Acme Product Importer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
app.include_router(products.router)
app.include_router(webhooks.router)
