"""Importe les modèles nécessaires à la construction du schéma SQLAlchemy."""
from app.models.role import Permission, Role, role_permissions, user_roles  # noqa: F401
from app.models.user import User  # noqa: F401
