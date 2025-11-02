from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Index
from sqlalchemy.sql import func
from . import Base
from sqlalchemy.orm import relationship

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jamendo_song_id = Column(String(50), nullable=False, index=True)  # ✅ Đổi thành String

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="likes", lazy="joined")
    __table_args__ = (
        Index('idx_user_jamendo_song', 'user_id', 'jamendo_song_id', unique=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "jamendo_song_id": self.jamendo_song_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": self.user.to_dict() if self.user else None
        }


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jamendo_song_id = Column(String(50), nullable=False, index=True)  # ✅ Đổi thành String
    content = Column(Text, nullable=False)
    user = relationship("User", back_populates="comments", lazy="joined")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "jamendo_song_id": self.jamendo_song_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": self.user.to_dict() if self.user else None
        }

