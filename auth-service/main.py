from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from database import engine, get_db

# Crée les tables si elles n'existent pas encore
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Vérifie que la connexion à MySQL fonctionne
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()