"""
Configuration de la base de données (SQLAlchemy).
Lit DATABASE_URL depuis .env (fallback sur SQLite si non défini, pratique pour dev).
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sso.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI : ouvre une session BDD par requête, la ferme ensuite."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()