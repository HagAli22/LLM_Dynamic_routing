"""Initialize Admin User - إنشاء مستخدم Admin"""

from database import SessionLocal, init_db, User, UserRole, APIKeySource
from auth import get_password_hash

def create_admin_user():
    """Create default admin user"""
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("⚠️  Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@llmrouter.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN,
            api_key_source=APIKeySource.SYSTEM_PROVIDED,
            monthly_query_limit=999999,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*60)
        print("Admin Credentials:")
        print("="*60)
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@llmrouter.com")
        print("="*60)
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
