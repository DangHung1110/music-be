from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your routers here
# from presentation.controllers.auth_controller import router as auth_router
# from presentation.controllers.music_controller import router as music_router

app = FastAPI(
    title="Music Streaming API",
    description="A modern music streaming backend built with FastAPI",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc"       # ReDoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
# app.include_router(music_router, prefix="/api/v1", tags=["Music"])

@app.get("/")
async def root():
    return {
        "message": "Music Streaming API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "message": "Service is up and running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
