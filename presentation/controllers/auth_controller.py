from fastapi import APIRouter, Depends, HTTPException, Header, Response, Cookie, Query
from fastapi.responses import RedirectResponse
from shared.decorators import async_handler
from shared.responses import OK, CREATED
from shared.exceptions import AuthFailureError
from business.services.auth_service import AuthService
from business.services.oauth_service import OAuthService
from presentation.validator.auth_validator import RegisterRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from presentation.middleware.auth_middleware import get_current_user
from datetime import datetime
from infrastructure.config.database import get_db, AsyncSession
from typing import Optional
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()
oauth_service = OAuthService()

@router.post("/register")
@async_handler
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.register_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    return CREATED(message="User registered successfully", metadata=result).send()

@router.post("/login")
@async_handler
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await auth_service.login_user(db=db, email=request.email, password=request.password)
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")

    # set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * int(os.getenv("REFRESH_TOKEN_EXPIRE", 7))  # seconds
    )

    return OK(metadata={"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}).send()

@router.get("/profile")
@async_handler
async def get_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_info = await auth_service.get_user_by_token(db, current_user)
    return OK(message="Profile retrieved successfully", metadata={"user": user_info}).send()

@router.post("/refresh")
@async_handler
async def refresh_token(response: Response, refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    new_tokens = await auth_service.refresh_access_token(refresh_token=refresh_token)

    # replace cookie with new refresh token if provided
    if "refresh_token" in new_tokens:
        response.set_cookie(
            key="refresh_token",
            value=new_tokens["refresh_token"],
            httponly=True,
            secure=bool(os.getenv("PRODUCTION", False)),
            samesite="lax",
            max_age=60 * 60 * 24 * int(os.getenv("REFRESH_TOKEN_EXPIRE", 7))
        )

    return OK(metadata={"access_token": new_tokens["access_token"], "token_type": "bearer"}).send()

@router.post("/logout")
@async_handler
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user),
    refresh_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
):
    # pass refresh_token and/or current access token to service for blacklist/invalidation
    await auth_service.logout_user(token=authorization, refresh_token=refresh_token)
    response.delete_cookie("refresh_token", path="/")
    return OK(message="Logged out").send()

@router.post("/logout-all")
@async_handler
async def logout_all_devices(
    current_user: dict = Depends(get_current_user),
    authorization: str = Header(None)
):
    # Extract token from authorization header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    if not token:
        raise AuthFailureError("Token not found in request")
    
    result = await auth_service.logout_all_devices(current_user["user_id"], token)
    return OK(message="Logged out from all devices", metadata=result).send()

@router.post("/forgot-password")
@async_handler
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.forgot_password(db, request.email)
    return OK(message="If the email exists, a reset link has been sent", metadata=result).send()

@router.post("/reset-password")
@async_handler
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.reset_password(
        db=db,
        reset_token=request.reset_token,
        new_password=request.new_password
    )
    return OK(message="Password reset successfully", metadata=result).send()

# OAuth endpoints
@router.get("/google")
@async_handler
async def google_auth():
    auth_url = oauth_service.get_google_auth_url()
    return OK(message="Redirect to Google OAuth", metadata={"auth_url": auth_url}).send()

@router.get("/facebook")
@async_handler
async def facebook_auth():
    auth_url = oauth_service.get_facebook_auth_url()
    return OK(message="Redirect to Facebook OAuth", metadata={"auth_url": auth_url}).send()

@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        # Exchange code for user info
        oauth_data = await oauth_service.exchange_google_code(code)
        
        # Handle login/registration
        result = await oauth_service.handle_oauth_login(db, oauth_data)
        
        # Build frontend redirect URL
        redirect_url = oauth_service.build_frontend_redirect_url(result)
        
        # Redirect to frontend with tokens
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        error_message = str(e)
        redirect_url = oauth_service.build_frontend_redirect_url({}, error_message)
        return RedirectResponse(url=redirect_url)

@router.get("/facebook/callback")
async def facebook_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        # Exchange code for user info
        oauth_data = await oauth_service.exchange_facebook_code(code)
        
        # Handle login/registration
        result = await oauth_service.handle_oauth_login(db, oauth_data)
        
        # Build frontend redirect URL
        redirect_url = oauth_service.build_frontend_redirect_url(result)
        
        # Redirect to frontend with tokens
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        error_message = str(e)
        redirect_url = oauth_service.build_frontend_redirect_url({}, error_message)
        return RedirectResponse(url=redirect_url)