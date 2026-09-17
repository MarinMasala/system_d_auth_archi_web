"""
Point d'entrée de l'application.
Lancer avec : uvicorn app.main:app --reload
Puis ouvrir http://127.0.0.1:8000/docs pour tester /register et /login
"""
from fastapi import FastAPI

from app import models  # noqa: F401  -- importe tous les modèles pour create_all
from app.auth.routes import router as auth_router
from app.database import Base, engine

# TODO P4 : from app.routers.pages_routes import router as pages_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DGFiP SSO — API d'authentification")

app.include_router(auth_router)
# TODO P4 : app.include_router(pages_router)


@app.get("/")
def root():
    return {"message": "API SSO DGFiP — voir /docs pour tester"}
