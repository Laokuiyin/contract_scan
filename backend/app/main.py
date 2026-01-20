from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import contracts, health
from app.core.db import engine, Base

app = FastAPI(title="Contract Scanner API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])

@app.get("/")
def read_root():
    return {"message": "Contract Scanner API"}
