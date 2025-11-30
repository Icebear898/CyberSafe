"""
CyberShield - Safe Haven Chat Backend
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    os.makedirs(settings.EVIDENCE_DIR, exist_ok=True)
    os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize admin user
    from app.core.database import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    try:
        admin_email = "admin@cybershield.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            print(f"Creating default admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                username="admin",
                full_name="System Admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_blocked=False,
                has_red_tag=False,
                warning_count=0
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created successfully")
        else:
            print(f"ℹ️ Admin user {admin_email} already exists")
    except Exception as e:
        print(f"❌ Failed to initialize admin user: {e}")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    pass


app = FastAPI(
    title="CyberShield API",
    description="Real-time AI-driven cyberbullying detection and mitigation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "CyberShield API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

