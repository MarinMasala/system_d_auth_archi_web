"""
Routes d'authentification.
Partie P2 : register, login, refresh-token, logout, /users/me.
Partie P3 (à ajouter dans ce même fichier, voir emplacements marqués ci-dessous) :
MFA (/mfa/send-otp, /mfa/verify-otp) et reset mot de passe (/forgot-password, /reset-password/{token}),
en s'appuyant sur otp_service.py et verification_service.py.
"""
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_valid_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas import LoginSchema, TokenResponse, UserCreate, UserOut

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginSchema, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        # TODO P5 : logger la tentative échouée dans connection_logs ici
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # TODO P3 : si MFA activé, ne pas poser les cookies tout de suite —
    # renvoyer un statut "mfa_required" et attendre /mfa/verify-otp avant
    # d'appeler create_access_token / create_refresh_token.

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user, db)

    # TODO P5 : logger la connexion réussie dans connection_logs ici

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        # secure=True,  # à activer dès que vous servez en HTTPS
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )

    return TokenResponse(access_token=access_token)


@router.post("/refresh-token", response_model=TokenResponse)
def refresh_token_route(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Pas de refresh token")

    db_token = get_valid_refresh_token(refresh_token, db)
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    new_access_token = create_access_token(user)
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        revoke_refresh_token(refresh_token, db)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Déconnecté"}


@router.get("/users/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Exemple de route protégée : démontre que get_current_user fonctionne."""
    return current_user


# ---------------------------------------------------------------------------
# EMPLACEMENT P3 — MFA & reset mot de passe
# À ajouter ici, en s'appuyant sur otp_service.py / verification_service.py :
#
# @router.post("/mfa/send-otp")
# def send_otp(...): ...
#
# @router.post("/mfa/verify-otp")
# def verify_otp(...): ...
#
# @router.post("/forgot-password")
# def forgot_password(...): ...
#
# @router.post("/reset-password/{token}")
# def reset_password(...): ...
# ---------------------------------------------------------------------------