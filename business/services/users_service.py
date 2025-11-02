from typing import Any, Dict, List, Optional

from infrastructure.config.database import AsyncSession
from data.repositories.user_repository import UserRepository
from shared.exceptions import NotFoundError, ConflictRequestError, BadRequestError
from business.services.auth_service import AuthService


class UsersService:
    def __init__(self):
        self.auth_service = AuthService()

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user.to_dict()

    async def list_users(self, db: AsyncSession, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        users = await user_repo.get_all(limit=limit, offset=offset)
        return {
            "users": [u.to_dict() for u in users],
            "limit": limit,
            "offset": offset,
            "count": len(users)
        }

    async def get_all_users(self, db: AsyncSession) -> List[Dict[str, Any]]:
        user_repo = UserRepository(db)
        users = await user_repo.get_all_users()
        return [user.to_dict() for user in users]

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
        image_url: Optional[str] = None,
        role: str = "user",
        is_active: bool = True,
    ) -> Dict[str, Any]:
        user_repo = UserRepository(db)

        # Uniqueness checks
        if await user_repo.get_by_email(email):
            raise ConflictRequestError("Email already registered")
        if await user_repo.get_by_username(username):
            raise ConflictRequestError("Username already taken")

        hashed_password = self.auth_service.hash_password(password)

        user = await user_repo.create({
            "username": username,
            "email": email,
            "password": hashed_password,
            "full_name": full_name,
            "bio": bio,
            "image_url": image_url,
            "role": role,
            "is_active": is_active,
        })

        return user.to_dict()

    async def update_user(
        self,
        db: AsyncSession,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        existing = await user_repo.get_by_id(user_id)
        if not existing:
            raise NotFoundError("User not found")

        # Handle unique fields updates
        if "email" in update_data and update_data["email"] != existing.email:
            if await user_repo.get_by_email(update_data["email"]):
                raise ConflictRequestError("Email already registered")
        if "username" in update_data and update_data["username"] != existing.username:
            if await user_repo.get_by_username(update_data["username"]):
                raise ConflictRequestError("Username already taken")

        if "password" in update_data and update_data["password"]:
            update_data["password"] = self.auth_service.hash_password(update_data["password"])

        updated = await user_repo.update(user_id, update_data)
        if not updated:
            raise BadRequestError("Failed to update user")
        return updated.to_dict()

    async def delete_user(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        user_repo = UserRepository(db)
        existing = await user_repo.get_by_id(user_id)
        if not existing:
            raise NotFoundError("User not found")
        await user_repo.delete(user_id)
        return {"deleted": True, "user_id": user_id}
