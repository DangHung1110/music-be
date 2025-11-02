import jwt
import os
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Dict, Any
from shared.exceptions import AuthFailureError, ConflictRequestError, NotFoundError
from data.repositories.user_repository import UserRepository
from infrastructure.external.email_servive import EmailService
from infrastructure.config.database import AsyncSession
from infrastructure.cache.redis_service import RedisService

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.email_service = EmailService()
        self.redis_service = RedisService()
        self.SECRET_KEY = os.getenv("JWT_SECRET", "your-fallback-secret-key")
        self.ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE", "7"))
        self.RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "60"))

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def generate_secure_token(self) -> str:
        return secrets.token_urlsafe(32)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_reset_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.RESET_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "reset"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("type") != token_type:
                raise AuthFailureError(f"Invalid token type. Expected {token_type}")
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthFailureError("Token has expired")
        except jwt.JWTError:
            raise AuthFailureError("Invalid token")

    async def register_user(self, db: AsyncSession, username: str, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        
        # Check login attempts (prevent spam registration)
        if await self.redis_service.is_login_locked(email):
            raise AuthFailureError("Too many attempts. Please try again later.")
        
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            await self.redis_service.track_login_attempt(email, success=False)
            raise ConflictRequestError("Email already registered")

        existing_username = await user_repo.get_by_username(username)
        if existing_username:
            await self.redis_service.track_login_attempt(email, success=False)
            raise ConflictRequestError("Username already taken")

        hashed_password = self.hash_password(password)

        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "full_name": full_name,
            "role": "user",
        }

        user = await user_repo.create(user_data)
        user_dict = user.to_dict()

        token_payload = {"user_id": user.id, "email": user.email, "username": user.username, "role": user.role}
        access_token = self.create_access_token(token_payload)
        refresh_token = self.create_refresh_token(token_payload)

        # Create Redis session
        session_id = await self.redis_service.create_session(user_dict, access_token)
        
        # Store refresh token
        await self.redis_service.store_refresh_token(user.id, refresh_token)
        
        # Cache user data
        await self.redis_service.cache_user_data(user.id, user_dict)
        
        # Track successful registration
        await self.redis_service.track_login_attempt(email, success=True)

        return {
            "user": user_dict,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }

    async def login_user(self, db: AsyncSession, email: str, password: str) -> Dict[str, Any]:
        # Check if login is locked due to too many attempts
        if await self.redis_service.is_login_locked(email):
            raise AuthFailureError("Account temporarily locked due to too many failed attempts. Please try again later.")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        
        if not user or not self.verify_password(password, user.password):
            await self.redis_service.track_login_attempt(email, success=False)
            raise AuthFailureError("Invalid email or password")
        
        if not user.is_active:
            await self.redis_service.track_login_attempt(email, success=False)
            raise AuthFailureError("Account has been deactivated")

        user_dict = user.to_dict()
        token_payload = {"user_id": user.id, "email": user.email, "username": user.username, "role": user.role}
        access_token = self.create_access_token(token_payload)
        refresh_token = self.create_refresh_token(token_payload)

        # Create Redis session
        session_id = await self.redis_service.create_session(user_dict, access_token)
        
        # Store refresh token
        await self.redis_service.store_refresh_token(user.id, refresh_token)
        
        # Cache user data
        await self.redis_service.cache_user_data(user.id, user_dict)
        
        # Track successful login
        await self.redis_service.track_login_attempt(email, success=True)

        return {
            "user": user_dict,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }

    async def logout_user(self, token: str, session_id: str = None, refresh_token: str = None) -> Dict[str, Any]:
        # Blacklist the token
        await self.redis_service.blacklist_token(token)
        
        # Revoke refresh token if provided
        if refresh_token:
            try:
                payload = self.verify_token(refresh_token, "refresh")
                user_id = payload.get("user_id")
                if user_id:
                    await self.redis_service.revoke_refresh_token(user_id, refresh_token)
            except:
                pass  
        
        # Delete session if provided
        if session_id:
            await self.redis_service.delete_session(session_id)
        
        return {"message": "Logged out successfully"}

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("user_id")
            
            if not user_id:
                raise AuthFailureError("Invalid refresh token")
            
            # Check if refresh token is still valid in Redis
            if not await self.redis_service.is_refresh_token_valid(user_id, refresh_token):
                raise AuthFailureError("Refresh token has been revoked")
            
            # Create new access token
            token_payload = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
            
            new_access_token = self.create_access_token(token_payload)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthFailureError("Refresh token has expired")
        except jwt.JWTError:
            raise AuthFailureError("Invalid refresh token")

    async def logout_all_devices(self, user_id: int, current_token: str) -> Dict[str, Any]:
        # Blacklist current token
        await self.redis_service.blacklist_token(current_token)
        
        # Delete all user sessions
        deleted_count = await self.redis_service.delete_all_user_sessions(user_id)
        
        # Revoke all refresh tokens for this user
        await self.redis_service.revoke_all_refresh_tokens(user_id)
        
        # Invalidate user cache
        await self.redis_service.invalidate_user_cache(user_id)
        
        return {
            "message": f"Logged out from {deleted_count} devices successfully"
        }

    async def verify_session_token(self, token: str) -> Dict[str, Any]:
        """Verify token and check if it's blacklisted"""
        # Check if token is blacklisted
        if await self.redis_service.is_token_blacklisted(token):
            raise AuthFailureError("Token has been revoked")
        
        # Verify token structure
        payload = self.verify_token(token)
        return payload

    async def forgot_password(self, db: AsyncSession, email: str) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(email)
        
        if not user or not user.is_active:
            return {"message": "If the email exists, a reset link has been sent."}

        reset_token = self.create_reset_token({"user_id": user.id, "email": user.email})
        reset_expires = datetime.utcnow() + timedelta(minutes=self.RESET_TOKEN_EXPIRE_MINUTES)

        await user_repo.update(user.id, {"reset_token": reset_token, "reset_expiration": reset_expires})

        try:
            await self.email_service.send_reset_password_email(email, reset_token, user.full_name or user.username)
        except Exception as e:
            print(f"Failed to send reset email: {e}")

        return {"message": "If the email exists, a reset link has been sent."}

    async def reset_password(self, db: AsyncSession, reset_token: str, new_password: str) -> Dict[str, Any]:
        try:
            payload = self.verify_token(reset_token, "reset")
            user_id = payload.get("user_id")
            if not user_id:
                raise AuthFailureError("Invalid reset token")

            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise AuthFailureError("Invalid reset token")

            if user.reset_token != reset_token or not user.reset_expiration or user.reset_expiration < datetime.utcnow():
                raise AuthFailureError("Reset token has expired or is invalid")

            hashed_password = self.hash_password(new_password)
            await user_repo.update(user.id, {"password": hashed_password, "reset_token": None, "reset_expiration": None})

            # Logout from all devices after password reset
            await self.logout_all_devices(user_id, "")

            try:
                await self.email_service.send_password_changed_notification(user.email, user.full_name or user.username)
            except Exception as e:
                print(f"Failed to send password changed notification: {e}")

            return {"message": "Password has been reset successfully"}

        except jwt.ExpiredSignatureError:
            raise AuthFailureError("Reset token has expired")
        except jwt.JWTError:
            raise AuthFailureError("Invalid reset token")

    async def get_user_by_token(self, db: AsyncSession, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = token_payload.get("user_id")
        if not user_id:
            raise AuthFailureError("Invalid token payload")

        # Try to get from cache first
        cached_user = await self.redis_service.get_cached_user_data(user_id)
        if cached_user:
            return cached_user

        # Get from database if not cached
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user_dict = user.to_dict()
        
        # Cache the user data
        await self.redis_service.cache_user_data(user_id, user_dict)
        
        return user_dict

