"""
Modèle User.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.role import user_roles


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    # Conservé pour compatibilité avec le JWT et le code existant.
    # La source d'autorisation RBAC est désormais user.roles.
    role = Column(String, default="contribuable", nullable=False)
    status = Column(String, default="active")
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )
