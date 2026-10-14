"""
Point d'entrée de l'application.
Lancer avec : uvicorn app.main:app --reload
Puis ouvrir http://127.0.0.1:8000/docs pour tester /register et /login
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  -- importe tous les modèles pour create_all
from app.auth.routes import router as auth_router
from app.database import Base, SessionLocal, engine
from app.models.role import seed_default_rbac
from app.routes.pages_routes import router as pages_router

Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    seed_default_rbac(_db)

app = FastAPI(title="DGFiP SSO — API d'authentification")

app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
app.include_router(auth_router)
app.include_router(pages_router)


@app.get("/")
def root():
    return RedirectResponse(url="/home")
