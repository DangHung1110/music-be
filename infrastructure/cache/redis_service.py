import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from infrastructure.config.redis import get_redis, redis_config
import redis.asyncio as redis

class RedisService:
    def __init__(self):
        self.session_prefix = "session:"
        self.token_blacklist_prefix = "blacklist:"
        self.user_sessions_prefix = "user_sessions:"
        self.login_attempts_prefix = "login_attempts:"
        self.refresh_tokens_prefix = "refresh_tokens:"
        
    async def get_redis_client(self) -> redis.Redis:
        return await get_redis()
    
    # Session management
    async def create_session(self, user_data: Dict[str, Any], token: str) -> str:
        redis_client = await self.get_redis_client()
        session_id = str(uuid.uuid4())
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data = {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "username": user_data.get("username"),
            "role": user_data.get("role", "user"),
            "token": token,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        await redis_client.setex(
            session_key,
            redis_config.SESSION_EXPIRE_SECONDS,
            json.dumps(session_data)
        )
        
        # Track user sessions for logout all devices
        user_sessions_key = f"{self.user_sessions_prefix}{user_data.get('user_id')}"
        await redis_client.sadd(user_sessions_key, session_id)
        await redis_client.expire(user_sessions_key, redis_config.SESSION_EXPIRE_SECONDS)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        redis_client = await self.get_redis_client()
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data = await redis_client.get(session_key)
        if not session_data:
            return None
            
        return json.loads(session_data)
    
    async def update_session_activity(self, session_id: str) -> bool:
        redis_client = await self.get_redis_client()
        session_key = f"{self.session_prefix}{session_id}"
        
        session_data = await redis_client.get(session_key)
        if not session_data:
            return False
            
        session = json.loads(session_data)
        session["last_activity"] = datetime.utcnow().isoformat()
        
        await redis_client.setex(
            session_key,
            redis_config.SESSION_EXPIRE_SECONDS,
            json.dumps(session)
        )
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        redis_client = await self.get_redis_client()
        session_key = f"{self.session_prefix}{session_id}"
        
        # Get session data to remove from user sessions
        session_data = await redis_client.get(session_key)
        if session_data:
            session = json.loads(session_data)
            user_sessions_key = f"{self.user_sessions_prefix}{session.get('user_id')}"
            await redis_client.srem(user_sessions_key, session_id)
        
        result = await redis_client.delete(session_key)
        return result > 0
    
    async def delete_all_user_sessions(self, user_id: int) -> int:
        redis_client = await self.get_redis_client()
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        
        session_ids = await redis_client.smembers(user_sessions_key)
        deleted_count = 0
        
        for session_id in session_ids:
            session_key = f"{self.session_prefix}{session_id}"
            if await redis_client.delete(session_key):
                deleted_count += 1
        
        await redis_client.delete(user_sessions_key)
        return deleted_count
    
    # Token blacklisting
    async def blacklist_token(self, token: str, expire_seconds: Optional[int] = None) -> bool:
        redis_client = await self.get_redis_client()
        blacklist_key = f"{self.token_blacklist_prefix}{token}"
        expire_time = expire_seconds or redis_config.TOKEN_BLACKLIST_EXPIRE_SECONDS
        
        await redis_client.setex(blacklist_key, expire_time, "blacklisted")
        return True
    
    async def is_token_blacklisted(self, token: str) -> bool:
        redis_client = await self.get_redis_client()
        blacklist_key = f"{self.token_blacklist_prefix}{token}"
        
        result = await redis_client.exists(blacklist_key)
        return result > 0
    
    # Login attempt tracking
    async def track_login_attempt(self, identifier: str, success: bool = False) -> Dict[str, Any]:
        redis_client = await self.get_redis_client()
        attempts_key = f"{self.login_attempts_prefix}{identifier}"
        
        attempts_data = await redis_client.get(attempts_key)
        if attempts_data:
            attempts = json.loads(attempts_data)
        else:
            attempts = {"count": 0, "last_attempt": None, "locked_until": None}
        
        attempts["count"] += 1
        attempts["last_attempt"] = datetime.utcnow().isoformat()
        
        # Lock account after 5 failed attempts for 15 minutes
        if not success and attempts["count"] >= 5:
            lock_until = datetime.utcnow() + timedelta(minutes=15)
            attempts["locked_until"] = lock_until.isoformat()
            
        # Reset on successful login
        if success:
            attempts = {"count": 0, "last_attempt": None, "locked_until": None}
        
        # Set expiry for 1 hour
        await redis_client.setex(attempts_key, 3600, json.dumps(attempts))
        return attempts
    
    async def is_login_locked(self, identifier: str) -> bool:
        redis_client = await self.get_redis_client()
        attempts_key = f"{self.login_attempts_prefix}{identifier}"
        
        attempts_data = await redis_client.get(attempts_key)
        if not attempts_data:
            return False
            
        attempts = json.loads(attempts_data)
        if not attempts.get("locked_until"):
            return False
            
        lock_until = datetime.fromisoformat(attempts["locked_until"])
        return datetime.utcnow() < lock_until
    
    # Caching user data
    async def cache_user_data(self, user_id: int, user_data: Dict[str, Any], expire_seconds: int = 300) -> bool:
        redis_client = await self.get_redis_client()
        cache_key = f"user_cache:{user_id}"
        
        await redis_client.setex(cache_key, expire_seconds, json.dumps(user_data))
        return True
    
    async def get_cached_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        redis_client = await self.get_redis_client()
        cache_key = f"user_cache:{user_id}"
        
        cached_data = await redis_client.get(cache_key)
        if not cached_data:
            return None
            
        return json.loads(cached_data)
    
    async def invalidate_user_cache(self, user_id: int) -> bool:
        redis_client = await self.get_redis_client()
        cache_key = f"user_cache:{user_id}"
        
        result = await redis_client.delete(cache_key)
        return result > 0
    
    # Refresh token management
    async def store_refresh_token(self, user_id: int, refresh_token: str, expire_seconds: int = None) -> bool:
        redis_client = await self.get_redis_client()
        refresh_key = f"{self.refresh_tokens_prefix}{user_id}"
        
        # Set expiry to 7 days by default
        expire_time = expire_seconds or (7 * 24 * 60 * 60)
        
        # Store the refresh token in a set for this user
        await redis_client.sadd(refresh_key, refresh_token)
        await redis_client.expire(refresh_key, expire_time)
        
        return True
    
    async def is_refresh_token_valid(self, user_id: int, refresh_token: str) -> bool:

        redis_client = await self.get_redis_client()
        refresh_key = f"{self.refresh_tokens_prefix}{user_id}"
        
        # Check if the refresh token exists in the user's set
        result = await redis_client.sismember(refresh_key, refresh_token)
        return result
    
    async def revoke_refresh_token(self, user_id: int, refresh_token: str) -> bool:
       
        redis_client = await self.get_redis_client()
        refresh_key = f"{self.refresh_tokens_prefix}{user_id}"
        
        result = await redis_client.srem(refresh_key, refresh_token)
        return result > 0
    
    async def revoke_all_refresh_tokens(self, user_id: int) -> bool:
   
        redis_client = await self.get_redis_client()
        refresh_key = f"{self.refresh_tokens_prefix}{user_id}"
        
        result = await redis_client.delete(refresh_key)
        return result > 0