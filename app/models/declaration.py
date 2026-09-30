"""
Modèle Declaration.
Une ligne = une déclaration fiscale soumise par un utilisateur.
Un utilisateur peut soumettre plusieurs déclarations (une par exercice fiscal, typiquement).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Session

from app.database import Base


class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fiscal_id = Column(String, nullable=False)
    year = Column(String, nullable=False)
    income_type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def create_declaration(
    db: Session,
    user_id: int,
    fiscal_id: str,
    year: str,
    income_type: str,
    amount: float,
    comments: str | None,
) -> Declaration:
    declaration = Declaration(
        user_id=user_id,
        fiscal_id=fiscal_id,
        year=year,
        income_type=income_type,
        amount=amount,
        comments=comments,
    )
    db.add(declaration)
    db.commit()
    db.refresh(declaration)
    return declaration