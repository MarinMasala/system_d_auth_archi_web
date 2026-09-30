from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/home", response_class=HTMLResponse, name="home_page")
def home_page(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={})


@router.get("/login", response_class=HTMLResponse, name="login_page")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@router.get("/register", response_class=HTMLResponse, name="register_page")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})


@router.get("/declaration", response_class=HTMLResponse, name="declaration_page")
def declaration_page(request: Request):
    return templates.TemplateResponse(request=request, name="declaration.html", context={})


@router.get("/dashboard", response_class=HTMLResponse, name="dashboard_page")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@router.get("/mfa", response_class=HTMLResponse, name="mfa_page")
def mfa_page(request: Request):
    return templates.TemplateResponse(request=request, name="mfa.html", context={})


@router.get("/forgot-password", response_class=HTMLResponse, name="forgot_password_page")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={})


@router.get("/error", response_class=HTMLResponse, name="error_page")
def error_page(request: Request):
    return templates.TemplateResponse(request=request, name="error.html", context={})
