"""Test that the model_name error is fixed"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_model_fix():
    """Test that the model_name dictionary access is fixed"""
    
    print("🔧 Testing model_name fix...")
    
    try:
        from database import get_db, UserAPIKey
        from crud import get_user_models_by_tier
        
        db = next(get_db())
        
        # Test get_user_models_by_tier function
        print("\n=== Testing get_user_models_by_tier ===")
        
        # Get first user (if any)
        test_user = db.query(UserAPIKey).first()
        if test_user:
            user_id = test_user.user_id
            print(f"Testing with user_id: {user_id}")
            
            user_models = get_user_models_by_tier(db, user_id)
            
            for tier, models in user_models.items():
                print(f"\n{tier}: {len(models)} models")
                for model in models:
                    print(f"  - model_path: {model.get('model_path', 'MISSING')}")
                    print(f"  - env_var_name: {model.get('env_var_name', 'MISSING')}")
                    
                    # Test accessing the keys that were causing errors
                    try:
                        _ = model['model_path']
                        _ = model['env_var_name']
                        print(f"  ✅ Dictionary access works")
                    except KeyError as e:
                        print(f"  ❌ KeyError: {e}")
        else:
            print("ℹ️  No user API keys found to test")
        
        db.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_fix()
