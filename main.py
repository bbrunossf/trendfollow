from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from app.core import config
from app.core.pipeline import run_pipeline

from app.api.routes import router as api_router

# =========================================================
# FastAPI app
# =========================================================

app = FastAPI(
    title="Trend Following API",
    description="API para análise de força relativa e ranking de ativos da B3",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


# ------------------------------------------------------------------
# Registro dos routers
# ------------------------------------------------------------------
app.include_router(api_router, prefix="/api")


# =========================================================
# Endpoints
# =========================================================

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
    
@app.get("/health")
def health_check():
    """
    Endpoint simples para verificação de status.
    """
    return {"status": "ok"}


@app.get("/run")
def run_trend_following(reference_date: Optional[str] = Query(
    default=None, description="Data de referência no formato YYYY-MM-DD")):
    """
    Executa o pipeline completo e retorna ranking e summary.
    """

    result = run_pipeline(reference_date=reference_date)

    return {
        "summary": result["summary"],
        "ranking": result["ranking"],
        "metadata": result.get("metadata", {}),
        "charts": result.get("charts", {})
    }
