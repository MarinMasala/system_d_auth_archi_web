<<<<<<< HEAD
=======
"""
Schémas Pydantic : ce que l'API accepte en entrée et renvoie en sortie.
P3 : ajoutez ici vos schémas OTP / reset password (OtpVerify, PasswordSchema, etc.)
"""
>>>>>>> origin/main
import re

from pydantic import BaseModel, EmailStr, field_validator

<<<<<<< HEAD
=======

>>>>>>> origin/main
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        """Politique de mot de passe : 12 caractères min, majuscule, chiffre, caractère spécial."""
        if len(v) < 12:
            raise ValueError("Le mot de passe doit contenir au moins 12 caractères")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
        return v

<<<<<<< HEAD
=======

>>>>>>> origin/main
class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    role: str

    class Config:
        from_attributes = True

<<<<<<< HEAD
=======

>>>>>>> origin/main
class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
<<<<<<< HEAD
    token_type: str = "bearer"
=======
    token_type: str = "bearer"
>>>>>>> origin/main
