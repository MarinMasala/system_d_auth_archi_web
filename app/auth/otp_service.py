"""
MFA — génération, envoi et vérification du code OTP à 6 chiffres (2e facteur au login).
Utilisé par POST /login (une fois le mot de passe validé) et POST /mfa/verify-otp.

Limite connue du MVP (à mentionner en soutenance) : pas de limite du nombre de
tentatives de code -- à ajouter (compteur + verrouillage) si le temps le permet.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.mail_config import send_email
from app.models.otp_code import OtpCode
from app.models.user import User

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_EXPIRE_MINUTES = 5


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


async def create_and_send_otp(user: User, db: Session) -> None:
    # un seul OTP valide à la fois : on invalide ceux encore actifs
    db.query(OtpCode).filter(
        OtpCode.user_id == user.id, OtpCode.used.is_(False)
    ).update({"used": True})

    code = _generate_code()
    otp = OtpCode(
        user_id=user.id,
        code_hash=_hash_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
        used=False,
    )
    db.add(otp)
    db.commit()

    try:
        await send_email(
            subject="Votre code de vérification DGFiP",
            recipient=user.email,
            body=(
                f"<p>Votre code de connexion est : <strong>{code}</strong></p>"
                f"<p>Ce code est valable {OTP_EXPIRE_MINUTES} minutes.</p>"
            ),
        )
    except Exception:
        logger.exception("Échec d'envoi de l'OTP à %s", user.email)
        # Contrairement à l'email de vérification, ici on prévient le client :
        # sans email reçu, il ne pourra jamais franchir l'étape /mfa/verify-otp.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Envoi du code de vérification impossible pour le moment, réessayez plus tard",
        )


def verify_otp(user_id: int, code: str, db: Session) -> None:
    otp = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user_id, OtpCode.used.is_(False))
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Aucun code en attente")
    if otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code expiré")
    if not secrets.compare_digest(otp.code_hash, _hash_code(code)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code incorrect")

    otp.used = True
    db.commit()
