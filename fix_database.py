"""Fix database migration issues"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database():
    """Run database migrations to fix missing columns"""
    
    print("🔧 Fixing database migrations...")
    
    try:
        # Import database functions
        from database import migrate_user_api_keys, migrate_messages, init_db
        
        # Run migrations
        print("📊 Running user_api_keys migration...")
        migrate_user_api_keys()
        
        print("📊 Running messages migration...")
        migrate_messages()
        
        print("📊 Initializing database...")
        init_db()
        
        print("\n✅ Database fixed successfully!")
        print("You can now restart the backend server.")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()
