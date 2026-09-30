"""
Modèles RBAC : rôles, permissions et tables d'association.

Une permission est identifiée par un scope (ex. ``declaration:write``).
Les utilisateurs héritent des permissions de leurs rôles via :
    users -> user_roles -> roles -> role_permissions -> permissions
"""
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.database import Base


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


DEFAULT_PERMISSIONS = (
    "declaration:read",
    "declaration:write",
    "users:manage",
)


def seed_default_rbac(db) -> None:
    """Crée les rôles/permissions MVP et rattache les anciens users à leur rôle."""
    from app.models.user import User

    roles = {}
    for role_name in ("contribuable", "agent"):
        role_obj = db.query(Role).filter(Role.name == role_name).first()
        if role_obj is None:
            role_obj = Role(name=role_name)
            db.add(role_obj)
            db.flush()
        roles[role_name] = role_obj

    permissions = {}
    for permission_name in DEFAULT_PERMISSIONS:
        permission = (
            db.query(Permission)
            .filter(Permission.name == permission_name)
            .first()
        )
        if permission is None:
            permission = Permission(name=permission_name)
            db.add(permission)
            db.flush()
        permissions[permission_name] = permission

    # Politique MVP :
    # - contribuable : consulter et créer/modifier ses déclarations
    # - agent : déclarations + gestion des utilisateurs
    for permission_name in ("declaration:read", "declaration:write"):
        if permissions[permission_name] not in roles["contribuable"].permissions:
            roles["contribuable"].permissions.append(permissions[permission_name])

    for permission in permissions.values():
        if permission not in roles["agent"].permissions:
            roles["agent"].permissions.append(permission)

    # Migration douce du champ User.role historique vers user_roles.
    for user in db.query(User).all():
        if not user.roles and user.role in roles:
            user.roles.append(roles[user.role])

    db.commit()
