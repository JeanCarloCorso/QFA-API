from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, analysis, screener, companies

app = FastAPI(
    title="QFA-API",
    description="Quantitative Financial Analysis API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1/health")
app.include_router(analysis.router, prefix="/api/v1/analysis")
app.include_router(screener.router, prefix="/api/v1/screener")
app.include_router(companies.router, prefix="/api/v1/companies")