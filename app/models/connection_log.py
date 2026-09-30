"""
Modèle ConnectionLog.
Trace chaque tentative de connexion (réussie ou échouée) pour l'audit de sécurité,
requis dans le cadre d'un système d'authentification forte.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from app.database import Base


class ConnectionLog(Base):
    __tablename__ = "connection_logs"

    id = Column(Integer, primary_key=True, index=True)
    # nullable : si l'email n'existe pas en base, on n'a pas de user_id à rattacher
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    email = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, nullable=False)  # "success" ou "failed"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def log_connection_attempt(
    db: Session,
    email: str,
    ip_address: str | None,
    user_agent: str | None,
    status: str,
    user_id: int | None = None,
) -> ConnectionLog:
    """Enregistre une tentative de connexion (succès ou échec)."""
    log_entry = ConnectionLog(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(log_entry)
    db.commit()
    return log_entry