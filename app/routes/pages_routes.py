from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.core import get_optional_user
from app.models.user import User

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.declaration import Declaration

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/home", response_class=HTMLResponse, name="home_page")
def home_page(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request=request, name="home.html", context={"user": user})


@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="login.html", context={"user": user})


@router.get("/register", response_class=HTMLResponse, name="register_page")
def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse(request=request, name="register.html", context={"user": user})


@router.get("/declaration", response_class=HTMLResponse, name="declaration_page")
def declaration_page(request: Request, user: User | None = Depends(get_optional_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="declaration.html", context={"user": user})


@router.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
def dashboard_page(request: Request, user: User | None = Depends(get_optional_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user})


@router.get("/mfa", response_class=HTMLResponse, name="mfa_page")
def mfa_page(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request=request, name="mfa.html", context={"user": user})


@router.get("/forgot-password", response_class=HTMLResponse, name="forgot_password_page")
def forgot_password_page(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={"user": user})


@router.get("/reset-password/{token}", response_class=HTMLResponse, name="reset_password_page")
def reset_password_page(
    request: Request,
    token: str,
    user: User | None = Depends(get_optional_user),
):
    response = templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={"user": user, "token": token},
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.get("/error", response_class=HTMLResponse, name="error_page")
def error_page(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request=request, name="error.html", context={"user": user})

@router.get("/historique", response_class=HTMLResponse, name="historique_page")
def historique_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if not user:
        return RedirectResponse(url="/login")

    declarations = (
        db.query(Declaration)
        .filter(Declaration.user_id == user.id)
        .order_by(Declaration.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request=request, name="historique.html", context={"user": user, "declarations": declarations}
    )