"""Test that user API keys are passed to fallback handlers"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_keys_fix():
    """Test that user API keys are correctly passed to fallback handlers"""
    
    print("🔑 Testing user API keys in fallback handlers...")
    
    try:
        from database import get_db, UserAPIKey
        from langgraph_router import LangGraphRouter
        
        db = next(get_db())
        
        # 1. Get user API keys from database
        print("\n=== User API Keys in Database ===")
        user_keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        api_keys_dict = {}
        for key in user_keys:
            print(f"User {key.user_id}: {key.model_name} -> {key.provider}")
            api_keys_dict[key.model_name] = f"API_KEY_FOR_{key.model_name}"
        
        # 2. Initialize router and check LLMClient
        print("\n=== Testing LLMClient API Keys ===")
        router = LangGraphRouter()
        
        if hasattr(router.llm_client, 'user_api_keys'):
            print(f"LLMClient has {len(router.llm_client.user_api_keys)} user API keys:")
            for model_path, api_key in router.llm_client.user_api_keys.items():
                print(f"  {model_path} -> {api_key[:20]}...")
        else:
            print("❌ LLMClient doesn't have user_api_keys attribute")
        
        # 3. Check fallback handlers
        print("\n=== Testing Fallback Handler API Keys ===")
        if hasattr(router.llm_client, 'fallback_handlers'):
            for tier, handler in router.llm_client.fallback_handlers.items():
                print(f"\n{tier} fallback handler:")
                print(f"  Models: {len(handler.models)}")
                print(f"  User API keys: {len(handler.user_api_keys)}")
                for model_path, api_key in handler.user_api_keys.items():
                    print(f"    {model_path} -> {api_key[:20]}...")
        else:
            print("❌ LLMClient doesn't have fallback_handlers")
        
        # 4. Test with user models
        print("\n=== Testing with User Models ===")
        from crud import get_user_models_by_tier
        
        if user_keys:
            test_user_id = user_keys[0].user_id
            user_models = get_user_models_by_tier(db, test_user_id)
            
            print(f"User {test_user_id} models:")
            for tier, models in user_models.items():
                if models:
                    print(f"  {tier}: {len(models)} models")
                    for model in models:
                        print(f"    {model.get('model_path', 'NO_PATH')} -> {model.get('api_key', 'NO_KEY')[:20]}...")
        
        db.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_keys_fix()
