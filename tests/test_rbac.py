import pytest
from fastapi import HTTPException

from app.auth.core import require_permission
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.role import Permission, Role, seed_default_rbac
from app.models.user import User


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_rbac_seed_creates_default_roles_permissions_and_migrates_users(db):
    user = User(email="contribuable@example.test", password_hash="x", role="contribuable")
    db.add(user)
    db.commit()

    seed_default_rbac(db)
    db.refresh(user)

    assert {role.name for role in user.roles} == {"contribuable"}
    assert {permission.name for permission in user.roles[0].permissions} == {
        "declaration:read",
        "declaration:write",
    }
    assert db.query(Role).count() == 2
    assert db.query(Permission).count() == 3


def test_require_permission_allows_and_denies(db):
    role = Role(name="agent")
    permission = Permission(name="declaration:write")
    role.permissions.append(permission)

    user = User(email="agent@example.test", password_hash="x", role="agent")
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert require_permission("declaration:write")(user) is user

    with pytest.raises(HTTPException) as exc:
        require_permission("users:manage")(user)
    assert exc.value.status_code == 403
