"""Création et consommation des liens de réinitialisation du mot de passe."""
import hashlib
import html
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.core import hash_password
from app.auth.mail_config import send_email
from app.models.password_reset_token import PasswordResetToken
from app.models.token import RefreshToken
from app.models.user import User

logger = logging.getLogger(__name__)

RESET_TOKEN_EXPIRE_HOURS = 1
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def create_and_send_password_reset_email(user: User, db: Session) -> None:
    raw_token = secrets.token_urlsafe(32)

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used.is_(False),
    ).update({PasswordResetToken.used: True}, synchronize_session=False)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS),
            used=False,
        )
    )
    db.commit()

    link = f"{APP_BASE_URL}/reset-password/{raw_token}"
    first_name = html.escape(user.first_name or "")
    try:
        await send_email(
            subject="Réinitialisation de votre mot de passe DGFiP",
            recipient=user.email,
            body=(
                f"<p>Bonjour {first_name},</p>"
                "<p>Une demande de réinitialisation du mot de passe de votre compte a été reçue.</p>"
                f"<p><a href=\"{link}\">Choisir un nouveau mot de passe</a></p>"
                f"<p>Ce lien est valable {RESET_TOKEN_EXPIRE_HOURS} heure. "
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>"
            ),
        )
    except Exception:
        logger.exception("Échec d'envoi de l'email de réinitialisation à %s", user.email)


def reset_password(raw_token: str, new_password: str, db: Session) -> None:
    token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == _hash_token(raw_token))
        .first()
    )
    if not token or token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien invalide ou déjà utilisé")

    expires_at = token.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce lien de réinitialisation a expiré")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur introuvable")

    user.password_hash = hash_password(new_password)
    token.used = True
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked.is_(False),
    ).update({RefreshToken.revoked: True}, synchronize_session=False)
    db.commit()