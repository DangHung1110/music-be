from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.sql import func
from datetime import datetime
from . import Base

class BaseMixin:
    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if isinstance(value, datetime):
                value = value.isoformat()  
            result[c.name] = value
        return result


class User(Base, BaseMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(100))
    bio = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    reset_token = Column(String(500), nullable=True)
    reset_expiration = Column(DateTime, nullable=True)
    role = Column(String(50), default="user")
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'facebook', etc.
    oauth_provider_id = Column(String(100), nullable=True)  

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
