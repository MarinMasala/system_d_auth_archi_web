"""
Configuration de la base de données (SQLAlchemy).
Lit DATABASE_URL, ou les variables DB_* utilisées par Docker, puis utilise
SQLite comme fallback pour le développement local.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    database_url = DATABASE_URL
elif os.getenv("DB_HOST"):
    database_url = URL.create(
        "mysql+pymysql",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.environ["DB_NAME"],
    )
else:
    database_url = "sqlite:///./sso.db"

database_driver = (
    database_url.drivername
    if isinstance(database_url, URL)
    else database_url.split(":", 1)[0]
)
connect_args = {"check_same_thread": False} if database_driver == "sqlite" else {}
engine = create_engine(database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI : ouvre une session BDD par requête, la ferme ensuite."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
