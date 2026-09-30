"""
Schémas Pydantic : ce que l'API accepte en entrée et renvoie en sortie.
"""
import re

from pydantic import BaseModel, EmailStr, field_validator


def _validate_password_policy(value: str) -> str:
    """Politique commune : 12 caractères, majuscule, chiffre et caractère spécial."""
    if len(value) < 12:
        raise ValueError("Le mot de passe doit contenir au moins 12 caractères")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule")
    if not re.search(r"[0-9]", value):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return _validate_password_policy(v)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    role: str

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return _validate_password_policy(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MfaRequired(BaseModel):
    mfa_required: bool = True
    mfa_token: str


class OtpVerify(BaseModel):
    mfa_token: str
    code: str
