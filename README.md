# Projet — Système d'authentification DGFiP (SSO)
*Architecture web — Groupe de 5 — Stack 100% Python (FastAPI)*

**Nom de groupe :** Les Jetons Fiscaux

---

## MVP — ce qu'on code vraiment (vous partez de zéro)

Ne visez pas tout le document d'un coup. Ce qui suit est le **scope réaliste** pour 5 étudiants sans base de code existante. Le reste (LDAP réel, 20M d'utilisateurs, Redis, réplication BDD) devient du **discours de rapport/oral**, pas du code à livrer.

### Stack recommandée — tout en Python

- **Backend : FastAPI** (routes API, validation avec Pydantic, doc auto via `/docs`)
- **Frontend : FastAPI + Jinja2** — FastAPI sert directement des templates HTML (`Jinja2Templates`), pas besoin de React/JS. C'est le choix le plus simple pour rester 100% Python et avoir un vrai rendu de pages.
  - *Alternative si le groupe veut plus "app" et moins "site web classique"* : **Streamlit** ou **NiceGUI** pour le frontend, qui parlent en HTTP à l'API FastAPI. Plus rapide à monter visuellement, mais moins représentatif d'une vraie archi front/back séparée pour un rapport d'architecture web. → **Jinja2 conseillé** si le prof évalue l'architecture, Streamlit/NiceGUI si l'évaluation est plus sur la fonctionnalité.
- **BDD : SQLite** pour développer vite, migration vers **PostgreSQL** possible en fin de projet si le temps le permet
- **ORM : SQLAlchemy** (+ **Alembic** pour les migrations si vous voulez montrer que vous savez faire évoluer un schéma)
- **Auth** :
  - `passlib[bcrypt]` → hash des mots de passe
  - `python-jose` (ou `PyJWT`) → génération/vérification des JWT
  - `fastapi-mail` ou `smtplib` (compte Gmail de test ou **Mailtrap**, gratuit et fait pour les tests → évite de spammer de vraies adresses) → envoi des OTP/reset
- **Validation des données** : Pydantic (natif à FastAPI, pas de lib en plus)
- **Serveur** : `uvicorn`
- **Tests** : `pytest` + `httpx` (client de test FastAPI)
- **Hébergement démo** : local en soutenance, ou Render/Railway (gratuit, supporte Python nativement)

### Scope MVP (à coder, semaines 1 à 5)

1. Inscription + login classique (email/mdp, hash bcrypt) — sans numéro fiscal au début, ajouté ensuite
2. JWT access + refresh token (votre "SSO" pédagogique — un jeton qui donne accès à 2 routes différentes suffit à démontrer le principe)
3. MFA email : code à 6 chiffres généré, envoyé par mail, vérifié côté serveur
4. Réinitialisation de mot de passe par email
5. RBAC minimal : 2 rôles (`contribuable`, `agent`), 2-3 permissions
6. Table `connection_logs` : une ligne par login (date, IP, user-agent)
7. Pages Jinja2 : accueil, login, déclaration, register, MFA, reset — formulaires HTML simples, CSS minimal

### Reste en discours (semaine 6, rapport + oral)

- LDAP réel → schéma expliqué, éventuellement un mock en dur (dictionnaire Python simulant un annuaire)
- 20M d'utilisateurs / pic de juin → expliquer ce qu'on ajouterait (Redis via `fastapi-cache` ou `redis-py`, plusieurs workers Uvicorn derrière un load balancer, DB en lecture répliquée) sans le construire
- Chiffrement avancé, multi-bâtiments → mentionnés dans l'archi cible

### Par où commencer, semaine 1

1. Tout le monde installe Python 3.11+, crée un environnement virtuel (`python -m venv venv`), installe `fastapi uvicorn sqlalchemy passlib[bcrypt] python-jose jinja2 python-multipart`
2. Structure de projet minimale :
   ```
   app/
     main.py
     models.py       (SQLAlchemy)
     schemas.py      (Pydantic)
     auth.py         (hash, JWT)
     database.py
     routers/
       auth_routes.py
       pages_routes.py
     templates/
       login.html
       home.html
     static/
   ```
3. Init Git, un `README.md` avec `uvicorn app.main:app --reload` pour lancer
4. P2 code juste `POST /register` + `POST /login` qui renvoie un JWT (testable sur `/docs`, généré automatiquement par FastAPI — gros avantage face à Node/Express pour la démo). Une fois que ça marche, le reste du groupe se greffe dessus.

---

## 0. Hypothèses de complément

- **Deux populations** : agents (comptes LDAP côté client, non implémenté — on suppose son existence) et contribuables (comptes rattachés à un numéro fiscal, gérés par nous).
- **MFA** = mot de passe (facteur 1) + code OTP par email (facteur 2). Pas de TOTP/SMS dans le scope de base.
- **Réinitialisation de mot de passe** : contribuables uniquement, pas les comptes LDAP.
- **Login contribuable** = numéro fiscal + mot de passe → le backend résout nom/prénom.
- **SSO** = un jeton central valable pour plusieurs routes/services de la même appli (démonstration du principe, pas un vrai fédération multi-domaines).
- **Pic de charge** : ~20M d'utilisateurs en juin, pic les 3 derniers jours → traité en discours d'architecture, pas en charge réelle testée.

---

## 1. Architecture générale

```
                 ┌─────────────────────┐
                 │  Navigateur          │
                 │  (pages Jinja2)      │
                 └──────────┬───────────┘
                             │ HTTPS
                 ┌──────────▼───────────┐
                 │   FastAPI (uvicorn)    │
                 │  ┌─────────────────┐  │
                 │  │ routers/pages   │  │  → sert le HTML (Jinja2)
                 │  ├─────────────────┤  │
                 │  │ routers/auth    │  │  → login, MFA, JWT, reset
                 │  ├─────────────────┤  │
                 │  │ routers/services│  │  → routes protégées par JWT
                 │  └─────────────────┘  │
                 └──────────┬───────────┘
                             │
                 ┌──────────▼───────────┐
                 │  SQLAlchemy (ORM)      │
                 └──────────┬───────────┘
                             │
                 ┌──────────▼───────────┐
                 │  SQLite / PostgreSQL   │
                 └───────────────────────┘

  (LDAP client = mocké, discours seulement — pas dans le schéma réel codé)
```

Principe SSO : login → JWT signé émis → le front (Jinja2) stocke le JWT en cookie HttpOnly → chaque requête vers une route protégée (`/declaration`, `/paiement`...) passe par une dépendance FastAPI (`Depends(get_current_user)`) qui vérifie le jeton, sans re-demander de mot de passe.

---

## 2. Planning & répartition (groupe de 5)

| Rôle | Personne | Responsabilités |
|---|---|---|
| **Chef de projet / Archi** | P1 | Cahier des charges, schéma d'archi, structure du repo FastAPI, coordination Git, soutenance |
| **Backend — Auth/SSO core** | P2 | `POST /register`, `POST /login`, JWT (création/vérification), dépendance `get_current_user`, refresh token |
| **Backend — MFA & permissions** | P3 | OTP email (`fastapi-mail`), politique de mots de passe (validation Pydantic), RBAC (rôles/permissions) |
| **Frontend (Jinja2)** | P4 | Templates HTML, formulaires, gestion des erreurs affichées, CSS minimal |
| **BDD & sécurité/logs** | P5 | Modèles SQLAlchemy, migrations Alembic, `connection_logs`, hashage, conformité RGPD |

### Planning type (6 semaines)

| Semaine | Étape | Livrable |
|---|---|---|
| 1 | Setup projet FastAPI, structure de dossiers, schéma d'archi | Repo qui démarre (`uvicorn --reload`), doc de conception |
| 2 | Modèles SQLAlchemy (`users`, `roles`...) + maquettes des templates | Schéma BDD validé, wireframes |
| 3 | `register` + `login` + JWT fonctionnels, testables sur `/docs` | API auth de base |
| 4 | OTP email, reset mdp, RBAC, début des templates Jinja2 | Endpoints complets + pages en dur |
| 5 | Intégration templates ↔ API, `connection_logs`, cookies HttpOnly | App connectée de bout en bout |
| 6 | Sécurité (HTTPS local via certif auto-signé, tests pytest), rapport, soutenance | Démo + rapport final |

---

## 3. Fonctionnalités

**Authentification**
- Connexion agent (identifiant + mdp, LDAP mocké) / connexion contribuable (numéro fiscal + mdp)
- SSO interne : un JWT donne accès à plusieurs routes protégées de l'appli
- MFA : mot de passe + code OTP email (validité 5 min)
- Réinitialisation de mot de passe (contribuables), lien à durée limitée
- Politique de mot de passe : 12 caractères min, majuscule, chiffre, caractère spécial (validation via `Pydantic` + `re`)

**Permissions & jetons**
- JWT signé (`python-jose`), payload avec `user_id`, `role`, `exp`
- RBAC via une dépendance FastAPI qui vérifie le rôle/permission avant d'exécuter la route
- Refresh token stocké en cookie HttpOnly, révocable en base

**Sécurité & traçabilité**
- HTTPS (certificat auto-signé en local pour la démo, à mentionner en prod réelle)
- Hash bcrypt pour les mots de passe, jamais en clair
- `connection_logs` : date, heure, IP, user-agent, statut, à chaque tentative de login

**Discours uniquement (pas codé)**
- Chiffrement AES-256 au repos, Redis, réplication BDD, load balancer, multi-bâtiments

---

## 4. Pages front-end (templates Jinja2)

**Minimum imposé**
1. `home.html` — page d'accueil
2. `login.html` — connexion
3. `declaration.html` — déclaration d'impôts (route protégée par JWT)

**Complémentaires nécessaires**
4. `register.html` — inscription (contribuable)
5. `mfa.html` — saisie du code OTP
6. `forgot_password.html` / `reset_password.html`
7. `dashboard.html` — liste des services accessibles via le token
8. `profile.html` — infos personnelles
9. `connection_history.html` — historique de connexions de l'utilisateur
10. `error.html` — 401/403 générique

**Admin (agent habilité)**
11. `admin_users.html` — gestion des comptes
12. `admin_logs.html` — supervision des logs de connexion

---

## 5. API / Backend (FastAPI)

```python
# auth_routes.py — exemples de signatures de routes

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    ...

@router.post("/login")
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    # vérifie mdp (bcrypt) ou bind LDAP mocké selon user.type
    # retourne un access_token + set-cookie refresh_token
    ...

@router.post("/mfa/send-otp")
def send_otp(user_id: int, db: Session = Depends(get_db)):
    ...

@router.post("/mfa/verify-otp")
def verify_otp(payload: OtpVerify, db: Session = Depends(get_db)):
    ...

@router.post("/refresh-token")
def refresh_token(request: Request):
    ...

@router.post("/logout")
def logout(response: Response):
    ...

@router.post("/forgot-password")
def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    ...

@router.post("/reset-password/{token}")
def reset_password(token: str, new_password: PasswordSchema, db: Session = Depends(get_db)):
    ...
```

**Routes protégées (exemple SSO)**
```python
@router.get("/declarations/me")
def my_declarations(current_user: User = Depends(get_current_user)):
    ...

@router.post("/declarations")
def create_declaration(
    data: DeclarationCreate,
    current_user: User = Depends(require_permission("declaration:write")),
):
    ...
```

**Autres routes**
- `GET /users/me`, `PUT /users/me`
- `GET /users` (admin), `PUT /users/{id}/role`, `PUT /users/{id}/lock`
- `GET /logs/connections/me`, `GET /logs/connections` (admin, filtrable)
- `GET /services` (services accessibles selon rôle du token)

Dépendances transverses FastAPI : `get_current_user` (décode/valide le JWT), `require_permission(scope)` (RBAC), `get_db` (session SQLAlchemy), middleware de rate limiting (ex. `slowapi`).

---

## 6. Base de données (SQLAlchemy)

**`users`**
`id (PK)`, `type` (agent/contribuable), `fiscal_number` (nullable, unique), `ldap_dn` (nullable), `password_hash` (nullable — contribuables seulement), `first_name`, `last_name`, `email`, `status`, `created_at`, `updated_at`

**`roles`** : `id`, `name`
**`permissions`** : `id`, `name`, `service_id (FK)`
**`role_permissions`** : `role_id (FK)`, `permission_id (FK)`
**`user_roles`** : `user_id (FK)`, `role_id (FK)`
**`services`** : `id`, `name`, `description`

**`otp_codes`**
`id`, `user_id (FK)`, `code_hash`, `expires_at`, `used`, `created_at`

**`tokens`**
`id`, `user_id (FK)`, `token_hash`, `type` (refresh/reset/activation), `expires_at`, `revoked`

**`connection_logs`**
`id`, `user_id (FK)`, `ip_address`, `device_info`, `status`, `timestamp`

```python
# models.py — exemple SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    type = Column(Enum("agent", "contribuable", name="user_type"))
    fiscal_number = Column(String, unique=True, nullable=True)
    ldap_dn = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 7. Points à traiter en soutenance / rapport

- Pourquoi FastAPI (perf, typage Pydantic, doc `/docs` auto générée pour démontrer l'API en live)
- Pourquoi JWT stateless plutôt que sessions serveur (scalabilité pour le pic de juin, même si non testée réellement)
- Comment le LDAP est mocké pour la démo (dictionnaire Python ou table simulant un annuaire)
- Flux SSO complet à montrer en live : login → MFA → JWT → accès à 2 routes protégées différentes avec le même jeton
- Ce qu'on ajouterait en prod réelle (Redis, plusieurs workers Uvicorn + Nginx en load balancer, réplication PostgreSQL) sans l'avoir codé
<<<<<<< HEAD
=======



# SSO DGFiP — Architecture commune du groupe

## Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

Copier `.env` et remplir `SECRET_KEY` avec une vraie valeur aléatoire (et vos
identifiants Mailtrap/Gmail une fois que P3 en a besoin).

## Lancer le serveur

```bash
uvicorn app.main:app --reload
```

Puis http://127.0.0.1:8000/docs pour tester `/register` et `/login`.

## Arborescence

```
sso-dgfip/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── app/
    ├── main.py
    ├── database.py
    ├── schemas.py
    ├── models/
    │   ├── user.py              (P2 — fait)
    │   ├── token.py             (P2 — fait, refresh token)
    │   ├── roles.py             (P3 — à compléter, RBAC)
    │   └── connection_log.py    (P5 — à compléter)
    ├── auth/
    │   ├── core.py              (P2 — fait : hash, JWT, refresh, get_current_user)
    │   ├── routes.py            (P2 — fait : register/login/refresh/logout
    │   │                          + emplacements marqués pour les routes MFA/reset de P3)
    │   ├── mail_config.py       (P3 — à compléter)
    │   ├── otp_service.py       (P3 — à compléter)
    │   └── verification_service.py (P3 — à compléter)
    ├── routers/
    │   └── pages_routes.py      (P4 — à compléter, sert les templates Jinja2)
    ├── templates/                (P4)
    └── static/                   (P4)
```

## Statut : testé et fonctionnel

Le flux register → login → route protégée (`/users/me` via `get_current_user`)
→ refresh-token → logout a été testé de bout en bout sur cette arborescence.

## Points d'intégration entre les parties

- **P3** : `User.role` existe déjà et est dans le payload JWT (`payload["role"]`).
  Ajoutez vos routes MFA/reset dans `app/auth/routes.py`, à l'emplacement marqué
  en bas du fichier. Pour un helper RBAC minimal en attendant le vôtre, il y a
  déjà `require_role()` dans `app/auth/core.py`.
- **P4** : les routes `/register` et `/login` sont prêtes, à brancher sur vos
  formulaires Jinja2 dans `app/routers/pages_routes.py`.
- **P5** : deux `# TODO P5` sont marqués dans `login()` (`app/auth/routes.py`)
  pour brancher `connection_logs` (succès et échec de connexion).

## À trancher en groupe

Le `docker-compose.yml` / architecture microservices (auth-service séparé,
prometheus...) vu dans une des propositions n'est pas dans le scope MVP du
projet (le document de cours dit explicitement que Docker/Redis restent du
"discours de rapport" à 5 sans base de code). À voir ensemble si vous voulez
vraiment partir là-dessus ou rester sur une seule app FastAPI comme ici.
>>>>>>> origin/main
