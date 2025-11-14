"""Debug what models are being passed to fallback handlers"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_fallback_models():
    """Debug the models being passed to fallback handlers"""
    
    print("🔍 Debugging fallback models...")
    
    try:
        from database import get_db, ModelRating
        from model_rating_system import ModelRatingManager
        from langgraph_router import LangGraphRouter
        
        db = next(get_db())
        
        # 1. Check database ranking
        print("\n=== Database Ranking (tier2) ===")
        manager = ModelRatingManager(db)
        leaderboard = manager.get_tier_leaderboard('tier2', limit=5)
        
        for item in leaderboard:
            print(f"#{item['rank']} {item['model_identifier']} → {item['score']} points")
        
        # 2. Check router models config
        print("\n=== Router Models Config ===")
        router = LangGraphRouter()
        
        for tier, models in router.models_config.items():
            print(f"\n{tier}: {len(models)} models")
            for i, model in enumerate(models, 1):
                print(f"  #{i} {model}")
        
        # 3. Check LLMClient models config
        print("\n=== LLMClient Models Config ===")
        if hasattr(router.llm_client, 'models_config'):
            for tier, models in router.llm_client.models_config.items():
                print(f"\n{tier}: {len(models)} models")
                for i, model in enumerate(models, 1):
                    if isinstance(model, (list, tuple)) and len(model) >= 2:
                        print(f"  #{i} {model[0]} → {model[1]}")
                    else:
                        print(f"  #{i} {model}")
        
        # 4. Check fallback handler models (THE IMPORTANT ONE)
        print("\n=== Fallback Handler Models ===")
        if hasattr(router.llm_client, 'fallback_handlers'):
            for tier, handler in router.llm_client.fallback_handlers.items():
                print(f"\n{tier}: {len(handler.models)} models")
                for i, model in enumerate(handler.models, 1):
                    if isinstance(model, (list, tuple)) and len(model) >= 2:
                        print(f"  #{i} {model[0]} → {model[1]}")
                    else:
                        print(f"  #{i} {model}")
        
        # 5. Check user API keys in fallback handler
        print("\n=== User API Keys in Fallback Handlers ===")
        if hasattr(router.llm_client, 'fallback_handlers'):
            for tier, handler in router.llm_client.fallback_handlers.items():
                print(f"\n{tier}: {len(handler.user_api_keys)} user API keys")
                for model_path, api_key in handler.user_api_keys.items():
                    print(f"  {model_path} -> {api_key[:20]}...")
        
        db.close()
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_fallback_models()
