"""
Routes d'authentification.
Partie P2 : register, login, refresh-token, logout, /users/me.
Partie P3 : MFA (/mfa/verify-otp) et activation de compte (/verify-email/{token}),
en s'appuyant sur otp_service.py et verification_service.py.
Reset mot de passe (/forgot-password, /reset-password/{token}) : pas encore fait,
voir emplacement marqué ci-dessous.
"""
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_mfa_token,
    create_refresh_token,
    decode_mfa_token,
    get_current_user,
    get_valid_refresh_token,
    hash_password,
    revoke_refresh_token,
    verify_password,
)
from app.auth.otp_service import create_and_send_otp, verify_otp
from app.auth.verification_service import create_and_send_verification_email, verify_email_token
from app.database import get_db
from app.models.user import User
from app.schemas import LoginSchema, MfaRequired, OtpVerify, TokenResponse, UserCreate, UserOut

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: Session = Depends(get_db)):
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

    await create_and_send_verification_email(db_user, db)
    return db_user


@router.get("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    verify_email_token(token, db)
    return {"detail": "Compte activé, vous pouvez vous connecter."}


def _issue_session_cookies(response: Response, user: User, db: Session) -> TokenResponse:
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user, db)

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


@router.post("/login", response_model=MfaRequired)
async def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        # TODO P5 : logger la tentative échouée dans connection_logs ici
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Compte non activé, vérifiez vos emails")

    # 1er facteur (mot de passe) validé : on envoie l'OTP et on attend /mfa/verify-otp
    # avant de poser les cookies de session.
    await create_and_send_otp(user, db)
    mfa_token = create_mfa_token(user)
    return MfaRequired(mfa_token=mfa_token)


@router.post("/mfa/verify-otp", response_model=TokenResponse)
def mfa_verify_otp(payload: OtpVerify, response: Response, db: Session = Depends(get_db)):
    user_id = decode_mfa_token(payload.mfa_token)
    verify_otp(user_id, payload.code, db)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    # TODO P5 : logger la connexion réussie dans connection_logs ici
    return _issue_session_cookies(response, user, db)


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
# EMPLACEMENT — reset mot de passe (pas encore fait)
#
# @router.post("/forgot-password")
# def forgot_password(...): ...
#
# @router.post("/reset-password/{token}")
# def reset_password(...): ...
# ---------------------------------------------------------------------------
