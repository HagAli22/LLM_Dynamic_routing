"""Fix missing database columns immediately"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_columns():
    """Add missing columns to user_api_keys table"""
    
    print("🔧 Fixing database columns...")
    
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Check current columns
            result = conn.execute(text("PRAGMA table_info(user_api_keys)"))
            columns = [row[1] for row in result]
            print(f"Current columns: {columns}")
            
            # Add missing columns
            if 'model_name' not in columns:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN model_name VARCHAR(200)"))
                print("✅ Added model_name column")
            
            if 'model_path' not in columns:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN model_path VARCHAR(300)"))
                print("✅ Added model_path column")
            
            if 'tier' not in columns:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN tier VARCHAR(20) DEFAULT 'tier1'"))
                print("✅ Added tier column")
            
            if 'input_price' not in columns:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN input_price FLOAT DEFAULT 0.0"))
                print("✅ Added input_price column")
            
            if 'output_price' not in columns:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN output_price FLOAT DEFAULT 0.0"))
                print("✅ Added output_price column")
            
            conn.commit()
            
            # Verify columns were added
            result = conn.execute(text("PRAGMA table_info(user_api_keys)"))
            new_columns = [row[1] for row in result]
            print(f"Updated columns: {new_columns}")
            
        print("\n✅ Database columns fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database_columns()
