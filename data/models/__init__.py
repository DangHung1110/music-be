from sqlalchemy.orm import declarative_base

# Tạo Base trước
Base = declarative_base()

# Import models sau để chúng dùng được Base
from .playlist import Playlist
from .music import Song