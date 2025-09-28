import os
import httpx
from typing import Dict, Any, Optional
from authlib.integrations.httpx_client import OAuth2Client
from shared.exceptions import AuthFailureError
from data.repositories.user_repository import UserRepository
from infrastructure.config.database import AsyncSession
from business.services.auth_service import AuthService

class OAuthService:
    def __init__(self):
        self.auth_service = AuthService()
        
        # Google OAuth config
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
        
        # Facebook OAuth config
        self.facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID")
        self.facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")
        self.facebook_redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/api/v1/auth/facebook/callback")
        
        # Frontend redirect URL
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        if not self.google_client_id:
            raise AuthFailureError("Google OAuth not configured")
            
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": self.google_redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

    def get_facebook_auth_url(self) -> str:
        """Generate Facebook OAuth authorization URL"""
        if not self.facebook_client_id:
            raise AuthFailureError("Facebook OAuth not configured")
            
        params = {
            "client_id": self.facebook_client_id,
            "redirect_uri": self.facebook_redirect_uri,
            "scope": "email",
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://www.facebook.com/v18.0/dialog/oauth?{query_string}"

    async def exchange_google_code(self, code: str) -> Dict[str, Any]:
        """Exchange Google authorization code for tokens and user info"""
        if not self.google_client_id or not self.google_client_secret:
            raise AuthFailureError("Google OAuth not configured")

        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": self.google_client_id,
            "client_secret": self.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.google_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            if token_response.status_code != 200:
                raise AuthFailureError("Failed to exchange Google authorization code")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                raise AuthFailureError("No access token received from Google")

            # Get user info from Google
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            user_response = await client.get(user_info_url, headers=headers)
            if user_response.status_code != 200:
                raise AuthFailureError("Failed to get user info from Google")
            
            user_info = user_response.json()
            
            return {
                "provider": "google",
                "provider_id": user_info.get("id"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "verified": user_info.get("verified_email", False)
            }

    async def exchange_facebook_code(self, code: str) -> Dict[str, Any]:
        """Exchange Facebook authorization code for tokens and user info"""
        if not self.facebook_client_id or not self.facebook_client_secret:
            raise AuthFailureError("Facebook OAuth not configured")

        # Exchange code for tokens
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        token_data = {
            "client_id": self.facebook_client_id,
            "client_secret": self.facebook_client_secret,
            "code": code,
            "redirect_uri": self.facebook_redirect_uri
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.get(token_url, params=token_data)
            if token_response.status_code != 200:
                raise AuthFailureError("Failed to exchange Facebook authorization code")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            
            if not access_token:
                raise AuthFailureError("No access token received from Facebook")

            # Get user info from Facebook
            user_info_url = "https://graph.facebook.com/v18.0/me"
            params = {
                "fields": "id,name,email,picture",
                "access_token": access_token
            }
            
            user_response = await client.get(user_info_url, params=params)
            if user_response.status_code != 200:
                raise AuthFailureError("Failed to get user info from Facebook")
            
            user_info = user_response.json()
            
            return {
                "provider": "facebook",
                "provider_id": user_info.get("id"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture", {}).get("data", {}).get("url"),
                "verified": True  # Facebook emails are verified by default
            }

    async def handle_oauth_login(self, db: AsyncSession, oauth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OAuth login/registration"""
        user_repo = UserRepository(db)
        
        # Check if user exists by email
        existing_user = await user_repo.get_by_email(oauth_data["email"])
        
        if existing_user:
            # User exists, check if they have OAuth provider linked
            if not existing_user.oauth_provider:
                # Link OAuth provider to existing account
                await user_repo.update(existing_user.id, {
                    "oauth_provider": oauth_data["provider"],
                    "oauth_provider_id": oauth_data["provider_id"]
                })
            
            # Generate tokens for existing user
            user_dict = existing_user.to_dict()
            token_payload = {
                "user_id": existing_user.id, 
                "email": existing_user.email, 
                "username": existing_user.username, 
                "role": existing_user.role
            }
            
            access_token = self.auth_service.create_access_token(token_payload)
            refresh_token = self.auth_service.create_refresh_token(token_payload)
            
            # Create Redis session
            session_id = await self.auth_service.redis_service.create_session(user_dict, access_token)
            await self.auth_service.redis_service.store_refresh_token(existing_user.id, refresh_token)
            await self.auth_service.redis_service.cache_user_data(existing_user.id, user_dict)
            
            return {
                "user": user_dict,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_id": session_id,
                "token_type": "bearer",
                "expires_in": self.auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_expires_in": self.auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            }
        else:
            # Create new user
            username = oauth_data["email"].split("@")[0]  # Use email prefix as username
            # Ensure username is unique
            counter = 1
            original_username = username
            while await user_repo.get_by_username(username):
                username = f"{original_username}{counter}"
                counter += 1
            
            user_data = {
                "username": username,
                "email": oauth_data["email"],
                "password": None,  # No password for OAuth users
                "full_name": oauth_data["name"],
                "role": "user",
                "oauth_provider": oauth_data["provider"],
                "oauth_provider_id": oauth_data["provider_id"],
                "is_active": True,
                "is_verified": oauth_data["verified"]
            }
            
            user = await user_repo.create(user_data)
            user_dict = user.to_dict()
            
            # Generate tokens
            token_payload = {
                "user_id": user.id, 
                "email": user.email, 
                "username": user.username, 
                "role": user.role
            }
            
            access_token = self.auth_service.create_access_token(token_payload)
            refresh_token = self.auth_service.create_refresh_token(token_payload)
            
            # Create Redis session
            session_id = await self.auth_service.redis_service.create_session(user_dict, access_token)
            await self.auth_service.redis_service.store_refresh_token(user.id, refresh_token)
            await self.auth_service.redis_service.cache_user_data(user.id, user_dict)
            
            return {
                "user": user_dict,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_id": session_id,
                "token_type": "bearer",
                "expires_in": self.auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_expires_in": self.auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            }

    def build_frontend_redirect_url(self, result: Dict[str, Any], error: Optional[str] = None) -> str:
        """Build frontend redirect URL with tokens or error"""
        if error:
            return f"{self.frontend_url}/auth/callback?error=true&message={error}"
        
        # Encode user data for URL
        import urllib.parse
        user_data = urllib.parse.quote(str(result["user"]))
        
        params = {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "session_id": result["session_id"],
            "expires_in": str(result["expires_in"]),
            "refresh_expires_in": str(result["refresh_expires_in"]),
            "user_data": user_data
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.frontend_url}/auth/callback?{query_string}"
