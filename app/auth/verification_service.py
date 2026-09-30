"""
Vérification d'email (activation de compte) — email envoyé juste après POST /register.
Tant que User.is_verified est False, /login refuse la connexion.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.mail_config import send_email
from app.models.user import User
from app.models.verification_token import EmailVerificationToken

logger = logging.getLogger(__name__)

VERIFICATION_EXPIRE_HOURS = 24
# TODO P4 : remplacer par l'URL réelle du frontend une fois les pages Jinja2 en place.
BASE_URL = "http://127.0.0.1:8000"


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def create_and_send_verification_email(user: User, db: Session) -> None:
    raw_token = secrets.token_urlsafe(32)
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRE_HOURS),
        used=False,
    )
    db.add(token)
    db.commit()

    link = f"{BASE_URL}/verify-email/{raw_token}"
    try:
        await send_email(
            subject="Confirmez votre compte DGFiP",
            recipient=user.email,
            body=(
                f"<p>Bienvenue {user.first_name or ''}, cliquez sur ce lien pour activer votre compte "
                f"(valable {VERIFICATION_EXPIRE_HOURS}h) :</p>"
                f"<p><a href='{link}'>{link}</a></p>"
            ),
        )
    except Exception:
        # Ne jamais faire échouer /register à cause d'un service mail indisponible/mal
        # configuré : le compte existe, le lien reste valide, il pourra être renvoyé.
        logger.exception("Échec d'envoi de l'email de vérification à %s", user.email)


def verify_email_token(raw_token: str, db: Session) -> User:
    token_hash = _hash_token(raw_token)
    token = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token_hash == token_hash)
        .first()
    )
    if not token or token.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien invalide")
    if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien expiré")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur introuvable")

    user.is_verified = True
    token.used = True
    db.commit()
    return user
