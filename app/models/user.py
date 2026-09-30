"""
Modèle User.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, default="contribuable")  # utilisé par P3 pour le RBAC
    status = Column(String, default="active")
    is_verified = Column(Boolean, default=False, nullable=False)  # email confirmé via lien d'activation
    created_at = Column(DateTime, default=datetime.utcnow)
