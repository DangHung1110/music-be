import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

# Tạo async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True
)

# Tạo async session
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base class cho models
Base = declarative_base()

# Dependency cho FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
