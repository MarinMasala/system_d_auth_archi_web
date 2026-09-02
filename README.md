# Projet-sys-d-auth
Projet FISA 2A 
# Projet — Système d'authentification DGFiP (SSO)
*Architecture web — Groupe de 5*

## 0. Hypothèses de complément

Vos notes ne couvrent pas tout : voici ce qui a été déduit/complété pour que l'archi tienne debout. À valider en groupe avant de coder.

- **Deux populations distinctes** : les **agents** (comptes déjà existants dans le **LDAP du client**) et les **contribuables** (comptes rattachés à un **numéro fiscal**, pas forcément dans le LDAP).
- **On n'implémente pas le serveur LDAP** : on suppose qu'il existe déjà côté client et on s'y connecte en **bind** (lecture/vérification), comme le précisent les notes. Notre appli est donc un **fournisseur d'identité (IdP) qui s'appuie sur le LDAP existant** pour les agents.
- **"MFA : mail et mdp"** est interprété comme : facteur 1 = mot de passe, facteur 2 = code à usage unique envoyé par email (OTP). Pas de TOTP/SMS mentionné, donc pas dans le scope de base (à proposer en bonus si le temps le permet).
- **Réinitialisation de mot de passe uniquement pour les comptes gérés par nous** (contribuables) : les mots de passe LDAP (agents) ne se réinitialisent pas depuis notre appli, c'est le rôle de l'IT interne / du client.
- **Login contribuable** = numéro fiscal + mot de passe → le backend résout nom/prénom associés en base et les renvoie au front pour affichage ("Bonjour M. Dupont").
- **SSO** = une fois connecté, l'utilisateur obtient un jeton central valable pour accéder à **plusieurs services** (ex. déclaration d'impôts, espace paiement, messagerie sécurisée...) sans se reconnecter à chacun.
- **Pic de charge** : ~20 millions d'utilisateurs sur le mois de juin, avec une explosion du trafic sur les 3 derniers jours avant la date limite de déclaration → l'architecture doit être pensée pour scaler horizontalement, pas juste "fonctionner".

---

## 1. Architecture générale

```
                         ┌─────────────────────┐
                         │   Client (front)     │
                         │  Agent / Contribuable │
                         └──────────┬───────────┘
                                    │ HTTPS
                         ┌──────────▼───────────┐
                         │   Load Balancer /      │
                         │   API Gateway          │
                         └──────────┬───────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
      ┌─────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
      │  Service Auth/SSO │ │  Service MFA/OTP │ │ Services métier │
      │  (IdP central)    │ │                  │ │ (déclaration,   │
      └─────────┬────────┘ └────────┬─────────┘ │ paiement, etc.) │
                │                   │            └────────┬────────┘
      ┌─────────▼────────┐ ┌────────▼─────────┐          │ vérifie le jeton SSO
      │  Connecteur LDAP   │ │  Cache Redis     │◄─────────┘
      │  (bind, lecture    │ │  (sessions,      │
      │  seule — agents)   │ │  tokens, rate    │
      └────────────────────┘  limiting)         │
                         └──────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  Base de données       │
                         │  (users, logs, tokens) │
                         └───────────────────────┘
```

Principe SSO : l'utilisateur s'authentifie **une seule fois** auprès du service Auth central, qui émet un **jeton d'accès (JWT) signé**, accepté par tous les services métier connectés (comme un mini-OAuth2/OpenID Connect maison). Chaque service métier vérifie le jeton (signature + scope/permissions) sans re-demander de mot de passe.

---

## 2. Planning & répartition (groupe de 5)

| Rôle | Personne | Responsabilités |
|---|---|---|
| **Chef de projet / Archi** | P1 | Cahier des charges, schéma d'archi, choix stack, coordination Git, plan de montée en charge, soutenance |
| **Backend — Auth/SSO core** | P2 | Login, connecteur LDAP (bind), login par numéro fiscal, émission/validation JWT, refresh token, logout SSO global |
| **Backend — MFA & permissions** | P3 | OTP email, politique de mots de passe, RBAC (rôles/permissions), jetons de service par service métier |
| **Frontend** | P4 | Pages agent + contribuable, formulaires, gestion des erreurs, redirections SSO entre services |
| **BDD, sécurité & logs** | P5 | Modèle de données, chiffrement, journalisation des connexions, stratégie de scalabilité (cache, réplication), conformité RGPD |

### Planning type (6 semaines)

| Semaine | Étape | Livrable |
|---|---|---|
| 1 | Cadrage : cas d'usage agent vs contribuable, schéma d'archi SSO/LDAP, choix stack | Doc de conception + schéma validé |
| 2 | Modèle de données + maquettes des 3 pages minimum + pages complémentaires | Schéma BDD, wireframes |
| 3 | Dev backend : login LDAP (simulé/mock), login numéro fiscal, JWT | API auth fonctionnelle (Postman) |
| 4 | Dev backend : OTP email, réinitialisation mdp, RBAC, jetons SSO multi-services | Endpoints complets |
| 5 | Intégration front/back, journal de connexions, tests de charge simulés | App connectée de bout en bout |
| 6 | Sécurité (HTTPS, chiffrement, rate limiting), tests, rapport, soutenance | Démo + rapport final |

---

## 3. Fonctionnalités

**Authentification**
- Connexion agent : identifiant + mot de passe → vérifié via **bind LDAP** côté client
- Connexion contribuable : **numéro fiscal + mot de passe** → backend résout nom/prénom en base
- SSO : un seul jeton valable pour accéder à plusieurs services métier
- Déconnexion locale (un service) et déconnexion globale (tous les services)
- MFA : mot de passe + **code OTP envoyé par email**, à durée de validité limitée (ex. 5 min)
- Réinitialisation de mot de passe (contribuables uniquement — pas les comptes LDAP)
- Politique de mot de passe imposée à la création/reset : **12 caractères minimum, au moins 1 majuscule, 1 chiffre, 1 caractère spécial**

**Permissions & jetons**
- Système de jetons signés (JWT) avec scope = liste des services autorisés
- RBAC : rôles (contribuable, agent, superviseur, admin) → permissions par service
- Révocation de jeton en cas de compromission / déconnexion globale

**Sécurité & traçabilité**
- Toute l'application en **HTTPS** (TLS)
- Chiffrement des données personnelles sensibles au repos (AES-256) et en transit (TLS)
- **Journal complet des connexions** : date, heure, utilisateur, IP, appareil, navigateur, statut (succès/échec)
- Détection de connexion suspecte (nouvel appareil, IP inhabituelle)
- Rate limiting / verrouillage après échecs répétés (anti brute-force)

**Montée en charge (pic de juin)**
- Architecture stateless (JWT) permettant d'ajouter des instances backend à la volée
- Cache Redis pour valider les jetons sans taper la base à chaque requête
- File d'attente asynchrone pour l'envoi des emails (OTP, reset) pour ne pas bloquer les logins en cas de pic
- Réplication en lecture de la base de données pour absorber la charge des logs/consultations

---

## 4. Pages front-end

**Minimum imposé par le sujet**
1. Page d'accueil
2. Page de connexion (login)
3. Page de déclaration d'impôts (service métier accessible après SSO)

**Complémentaires nécessaires pour que le système tienne**
4. Vérification MFA (saisie du code OTP reçu par email)
5. Mot de passe oublié (contribuables)
6. Réinitialisation du mot de passe
7. Première connexion / activation de compte (le contribuable reçoit un numéro fiscal et doit définir son mot de passe la première fois)
8. Tableau de bord contribuable (liste des services accessibles via SSO : déclaration, paiement, messagerie…)
9. Tableau de bord agent (vue différente selon rôle)
10. Profil / informations personnelles
11. Historique des connexions (dates, heures, appareils) consultable par l'utilisateur
12. Page d'erreur / accès refusé
13. Page de maintenance (utile en cas de bâtiment en rénovation ou de surcharge ponctuelle)

**Espace administrateur (agent habilité)**
14. Gestion des comptes contribuables (recherche, déblocage, désactivation)
15. Gestion des rôles/permissions
16. Supervision des logs de connexion et alertes de sécurité

---

## 5. API / Backend

REST, JWT stateless (Authorization header), refresh token en cookie HttpOnly, HTTPS obligatoire partout.

**Auth / SSO**
- `POST /api/auth/login/agent` → vérifie via LDAP (bind), retourne un JWT si OK
- `POST /api/auth/login/contribuable` → vérifie numéro fiscal + mdp en base
- `POST /api/auth/mfa/send-otp` → envoie le code par email
- `POST /api/auth/mfa/verify-otp` → valide le code, finalise l'émission du JWT
- `POST /api/auth/refresh-token`
- `POST /api/auth/logout` (local)
- `POST /api/auth/logout-all` (SSO global — révoque tous les jetons de l'utilisateur)
- `POST /api/auth/forgot-password` (contribuable uniquement)
- `POST /api/auth/reset-password/:token`
- `POST /api/auth/activate/:fiscal_number` (première connexion / création du mot de passe)

**Permissions / services**
- `GET /api/services` (services accessibles selon le rôle du token)
- `POST /api/services/:id/access-token` (jeton scoped pour un service précis, pattern SSO)
- `GET /api/permissions/me`

**Utilisateurs**
- `GET /api/users/me`
- `PUT /api/users/me`
- `GET /api/users` (admin)
- `PUT /api/users/:id/role` (admin)
- `PUT /api/users/:id/lock` / `unlock` (admin)

**Traçabilité**
- `GET /api/logs/connections/me` (historique perso)
- `GET /api/logs/connections` (admin/superviseur, filtrable par date/utilisateur/site)

**Service métier (exemple, pour montrer l'intégration SSO)**
- `GET /api/declarations/me`
- `POST /api/declarations` → nécessite un JWT valide avec le scope `declaration:write`

Middlewares transverses : `authMiddleware` (vérifie signature JWT), `rbacMiddleware` (vérifie le scope/permission), `rateLimiter`, `ldapConnector` (proxy vers LDAP en lecture seule), `otpService`, `deviceLogger`.

---

## 6. Base de données

**`users`**
`id (PK)`, `type` (agent/contribuable), `fiscal_number` (nullable, contribuables uniquement, unique), `ldap_dn` (nullable, agents uniquement — référence vers l'entrée LDAP, pas de mot de passe stocké pour eux), `password_hash` (nullable — uniquement pour contribuables), `first_name`, `last_name`, `email`, `status` (pending/active/locked/disabled), `created_at`, `updated_at`

> Un agent n'a **jamais** de `password_hash` en local : son mot de passe vit dans le LDAP. Un contribuable **n'a jamais** de `ldap_dn`.

**`roles`**
`id (PK)`, `name` (admin, agent, superviseur, contribuable)

**`permissions`**
`id (PK)`, `name`, `service_id (FK)`

**`role_permissions`**
`role_id (FK)`, `permission_id (FK)`

**`user_roles`**
`user_id (FK)`, `role_id (FK)`

**`services`**
`id (PK)`, `name`, `description`, `base_url`

**`otp_codes`**
`id (PK)`, `user_id (FK)`, `code_hash`, `expires_at`, `used` (bool), `created_at`

**`tokens`**
`id (PK)`, `user_id (FK)`, `token_hash`, `type` (refresh/service/reset/activation), `service_id (FK, nullable)`, `expires_at`, `revoked` (bool)

**`sessions`**
`id (PK)`, `user_id (FK)`, `device_info`, `os`, `browser`, `ip_address`, `site_id (FK, nullable)`, `created_at`, `last_active_at`, `is_active` (bool)

**`connection_logs`**
`id (PK)`, `user_id (FK)`, `ip_address`, `device_info`, `site_id (FK, nullable)`, `status` (success/failed), `timestamp`

**`sites`**
`id (PK)`, `name`, `address`, `status` (operational/renovation/closed)

**Notes de conception**
- `password_hash` (contribuables) : argon2 ou bcrypt, jamais en clair
- Chiffrement AES-256 au repos pour les champs sensibles (numéro fiscal, nom/prénom si exigé par la politique de sécurité du projet)
- Index sur `fiscal_number`, `user_id` (sessions/connection_logs) pour absorber la charge de juin
- Partitionnement ou archivage périodique de `connection_logs` (volume énorme avec 20M d'utilisateurs/mois)
- Politique de rétention des logs à définir dans le rapport (durée légale RGPD)

---

## 7. Points à traiter en soutenance / rapport (sécurité + charge)

- Pourquoi JWT stateless plutôt que sessions serveur classiques (scalabilité horizontale pour le pic de juin)
- Pourquoi le cache Redis est indispensable pour ne pas saturer la BDD en période de pointe
- Comment le connecteur LDAP est mocké pour la démo (vous n'avez pas de vrai serveur LDAP du client)
- Schéma de flux SSO complet (login → MFA → JWT → accès à 2 services différents avec le même jeton)
- Justification du choix HTTPS partout + chiffrement au repos (obligation légale, données fiscales = données sensibles)
