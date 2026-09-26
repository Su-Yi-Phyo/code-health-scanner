"""
FastAPI application entry point.

Run locally:
    uvicorn backend.main:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.phase3.router import router as phase3_router

app = FastAPI(
    title="Python Code Health Scanner",
    description="Analyzes public GitHub Python repositories and returns risk scores.",
    version="0.1.0",
)

# Allow the Next.js dev server (and Vercel) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(phase3_router)


@app.get("/health", tags=["Meta"])
def health() -> dict:
    return {"status": "ok"}
