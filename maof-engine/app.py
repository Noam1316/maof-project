"""
Maof Engine — FastAPI App
הרצה: uvicorn app:app --reload
"""

import sys
sys.path.insert(0, ".")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="Maof — Dual Scoring Engine",
    description="מנוע שיבוץ AI לחיילים משוחררים | מעוף Tech-Lead Israel",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "Maof Dual Scoring Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "score": "POST /api/v1/score",
            "match": "POST /api/v1/match",
            "simulate": "POST /api/v1/simulate",
            "simulate_quick": "GET /api/v1/simulate/quick",
        }
    }
