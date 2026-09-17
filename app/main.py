<<<<<<< HEAD
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_fastapi_instrumentator import Instrumentator
import models
from auth import schemas
from database import engine, get_db, Base
from auth.security import hash_password, verify_password, create_access_token

Base.metadata.create_all(bind=engine)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DGFiP SSO — API d'authentification")
Instrumentator().instrument(app).expose(app)

app.include_router(auth_router)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}

@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    new_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
=======
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
>>>>>>> origin/main
