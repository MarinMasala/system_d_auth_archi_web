"""
Modèle RefreshToken.
On ne stocke jamais le token en clair : on garde son hash, pour pouvoir
le révoquer (logout) sans jamais avoir à réutiliser sa valeur brute.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Note pour P3 : les tokens de type "reset" (mot de passe oublié) et "activation"
# peuvent réutiliser cette même table (ajouter une colonne `type`) ou une table à part
# selon ce que vous préférez — à voir ensemble.
