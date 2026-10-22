import asyncio
import re
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import otp_service
from app.database import Base
from app.models.otp_code import OtpCode
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


def create_user_with_pending_otp(db):
    user = User(email="otp@example.test", password_hash="x")
    db.add(user)
    db.flush()

    previous_otp = OtpCode(
        user_id=user.id,
        code_hash=otp_service._hash_code("123456"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        used=False,
    )
    db.add(previous_otp)
    db.commit()
    return user, previous_otp


def test_failed_email_keeps_previous_otp_valid(db, monkeypatch):
    user, previous_otp = create_user_with_pending_otp(db)

    async def fail_to_send(**_kwargs):
        raise RuntimeError("SMTP rate limited")

    monkeypatch.setattr(otp_service, "send_email", fail_to_send)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(otp_service.create_and_send_otp(user, db))

    assert exc.value.status_code == 503
    db.refresh(previous_otp)
    assert previous_otp.used is False
    assert db.query(OtpCode).count() == 1


def test_successful_email_replaces_previous_otp(db, monkeypatch):
    user, previous_otp = create_user_with_pending_otp(db)
    sent_code = None

    async def capture_email(**kwargs):
        nonlocal sent_code
        sent_code = re.search(r"<strong>(\d{6})</strong>", kwargs["body"]).group(1)

    monkeypatch.setattr(otp_service, "send_email", capture_email)
    asyncio.run(otp_service.create_and_send_otp(user, db))

    db.refresh(previous_otp)
    assert previous_otp.used is True
    assert db.query(OtpCode).filter_by(user_id=user.id, used=False).count() == 1

    otp_service.verify_otp(user.id, sent_code, db)
    assert db.query(OtpCode).filter_by(user_id=user.id, used=False).count() == 0
