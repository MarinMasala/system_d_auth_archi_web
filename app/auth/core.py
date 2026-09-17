"""
Coeur de l'authentification (partie P2) :
- hash / vérification des mots de passe (bcrypt)
- création / décodage des JWT (access token)
- création / vérification / révocation des refresh tokens
- dépendance get_current_user réutilisable par tout le groupe pour protéger des routes
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.token import RefreshToken
from app.models.user import User

load_dotenv()

# --- Config JWT ---------------------------------------------------------
# Valeurs lues depuis .env ; fallback de dev uniquement, à ne jamais garder en prod/soutenance.
SECRET_KEY = os.getenv("SECRET_KEY", "change-moi-avant-la-soutenance")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


# --- Mots de passe -------------------------------------------------------
# bcrypt utilisé directement (passlib a des soucis de compatibilité avec
# les versions récentes de la lib bcrypt).

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# --- Access token (JWT) ---------------------------------------------------

def create_access_token(user: User) -> str:
    """Crée le JWT du 'SSO' : payload avec user_id, role, exp."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )


# --- Refresh token ---------------------------------------------------------
# On ne stocke jamais le refresh token en clair en base : on garde son hash SHA-256.

def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_refresh_token(user: User, db: Session) -> str:
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(db_token)
    db.commit()
    return raw_token


def get_valid_refresh_token(raw_token: str, db: Session) -> RefreshToken:
    token_hash = _hash_token(raw_token)
    db_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if not db_token or db_token.revoked:
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expiré")
    return db_token


def revoke_refresh_token(raw_token: str, db: Session) -> None:
    token_hash = _hash_token(raw_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if db_token:
        db_token.revoked = True
        db.commit()


# --- Dépendance get_current_user -------------------------------------------
# Utilisée par TOUT LE GROUPE pour protéger n'importe quelle route :
#   from app.auth.core import get_current_user
#   @router.get("/declarations/me")
#   def my_declarations(current_user: User = Depends(get_current_user)):
#       ...

def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Non authentifié")

    payload = decode_access_token(access_token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


def require_role(role: str):
    """
    Petit helper RBAC de base, en attendant celui plus complet de P3.
    Usage : Depends(require_role("agent"))
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return current_user
<<<<<<< HEAD
    return checker
=======
    return checker
>>>>>>> origin/main
