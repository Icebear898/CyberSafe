#!/usr/bin/env python3
"""
CyberShield - Admin Account Creation Script
Creates an admin user account in the database
"""
import sys
import os
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin_user():
    """Create an admin user account"""
    print("🔐 CyberShield Admin Account Creation")
    print("=" * 50)
    
    # Get admin details
    email = input("Enter admin email: ").strip()
    if not email or '@' not in email:
        print("❌ Invalid email address")
        return
    
    username = input("Enter admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    full_name = input("Enter admin full name (optional): ").strip()
    
    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        print("❌ Passwords do not match")
        return
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        return
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"❌ User with email '{email}' or username '{username}' already exists")
            
            # Ask if they want to make existing user an admin
            make_admin = input("Do you want to make this user an admin? (y/n): ").strip().lower()
            if make_admin == 'y':
                existing_user.role = UserRole.ADMIN
                db.commit()
                print(f"✅ User '{existing_user.username}' is now an admin!")
            return
        
        # Create new admin user
        hashed_password = get_password_hash(password)
        
        admin_user = User(
            email=email,
            username=username,
            full_name=full_name if full_name else username,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_blocked=False,
            has_red_tag=False,
            warning_count=0
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("\n✅ Admin account created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role}")
        print(f"\n🚀 You can now log in with these credentials")
        
    except Exception as e:
        print(f"❌ Error creating admin account: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
