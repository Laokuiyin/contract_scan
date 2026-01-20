"""
Main application entry point for Contract Scanner API
"""
from fastapi import FastAPI

app = FastAPI(
    title="Contract Scanner API",
    description="API for scanning and analyzing contract documents",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Contract Scanner API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
