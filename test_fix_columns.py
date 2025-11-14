"""Test that all required columns exist"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_columns():
    """Test that all required columns exist in user_api_keys table"""
    
    print("🔍 Testing database columns...")
    
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Check current columns
            result = conn.execute(text("PRAGMA table_info(user_api_keys)"))
            columns = [row[1] for row in result]
            
            print(f"Current columns: {columns}")
            
            required_columns = ['model_name', 'model_path', 'tier', 'input_price', 'output_price']
            missing_columns = []
            
            for col in required_columns:
                if col not in columns:
                    missing_columns.append(col)
                else:
                    print(f"✅ {col} exists")
            
            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
                print("Please run: python fix_database_columns.py")
            else:
                print("\n✅ All required columns exist!")
                
                # Test accessing a UserAPIKey object
                try:
                    from database import get_db, UserAPIKey
                    db = next(get_db())
                    
                    # Try to get first user key (if any)
                    test_key = db.query(UserAPIKey).first()
                    if test_key:
                        print(f"✅ Successfully accessed UserAPIKey object")
                        print(f"   - model_name: {getattr(test_key, 'model_name', 'MISSING')}")
                        print(f"   - model_path: {getattr(test_key, 'model_path', 'MISSING')}")
                        print(f"   - tier: {getattr(test_key, 'tier', 'MISSING')}")
                    else:
                        print("ℹ️  No UserAPIKey records found to test")
                    
                    db.close()
                    
                except Exception as e:
                    print(f"❌ Error accessing UserAPIKey: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_columns()
