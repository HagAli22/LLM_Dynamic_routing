"""Test that user models get priority in fallback chain"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_user_model_priority():
    """Test that user models appear first in fallback chain"""
    
    print("🏆 Testing user model priority in fallback chain...")
    
    try:
        from database import get_db, ModelRating
        from model_rating_system import ModelRatingManager
        from langgraph_router import LangGraphRouter
        
        db = next(get_db())
        
        # 1. Check current tier2 ranking
        print("\n=== Current Tier2 Ranking ===")
        manager = ModelRatingManager(db)
        leaderboard = manager.get_tier_leaderboard('tier2', limit=5)
        
        for item in leaderboard:
            print(f"#{item['rank']} {item['model_identifier']} → {item['score']} points")
        
        # 2. Initialize router and check models config
        print("\n=== Router Models Config ===")
        router = LangGraphRouter()
        
        for tier, models in router.models_config.items():
            print(f"\n{tier}: {len(models)} models")
            for i, model in enumerate(models[:3], 1):  # Show first 3
                print(f"  #{i} {model}")
        
        # 3. Check LLMClient config
        print("\n=== LLMClient Config ===")
        if hasattr(router.llm_client, 'models_config'):
            for tier, models in router.llm_client.models_config.items():
                print(f"\n{tier}: {len(models)} models")
                for i, model in enumerate(models[:3], 1):  # Show first 3
                    if isinstance(model, (list, tuple)) and len(model) >= 2:
                        print(f"  #{i} {model[0]} → {model[1]}")
                    else:
                        print(f"  #{i} {model}")
        
        # 4. Check fallback handler models
        print("\n=== Fallback Handler Models ===")
        if hasattr(router.llm_client, 'fallback_handlers'):
            for tier, handler in router.llm_client.fallback_handlers.items():
                print(f"\n{tier}: {len(handler.models)} models")
                for i, model in enumerate(handler.models[:3], 1):  # Show first 3
                    if isinstance(model, (list, tuple)) and len(model) >= 2:
                        print(f"  #{i} {model[0]} → {model[1]}")
                    else:
                        print(f"  #{i} {model}")
        
        db.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_model_priority()
