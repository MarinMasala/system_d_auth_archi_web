"""
Configuration et envoi d'emails (fastapi-mail).
Utilisé par otp_service.py (MFA), verification_service.py (activation) et
password_reset_service.py (réinitialisation du mot de passe).

En dev : créer un compte Mailtrap (gratuit, https://mailtrap.io) et renseigner
ses identifiants "sandbox" dans .env pour ne jamais envoyer de vrais emails :
  MAIL_USERNAME=...
  MAIL_PASSWORD=...
  MAIL_FROM=no-reply@dgfip-sso.local
  MAIL_SERVER=sandbox.smtp.mailtrap.io
  MAIL_PORT=2525
"""
import os

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "no-reply@dgfip-sso.fr"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "2525")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "sandbox.smtp.mailtrap.io"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(conf)


async def send_email(subject: str, recipient: str, body: str) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
    )
    await fast_mail.send_message(message)
