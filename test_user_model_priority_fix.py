"""Test that user models get priority after the fix"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_user_model_priority_fix():
    """Test that user models appear first in fallback chain after fix"""
    
    print("🏆 Testing user model priority fix...")
    
    try:
        from database import get_db, ModelRating, UserAPIKey
        from model_rating_system import ModelRatingManager
        from langgraph_router import LangGraphRouter
        from crud import get_user_models_by_tier
        
        db = next(get_db())
        
        # 1. Check current tier2 ranking
        print("\n=== Current Tier2 Ranking ===")
        manager = ModelRatingManager(db)
        leaderboard = manager.get_tier_leaderboard('tier2', limit=5)
        
        for item in leaderboard:
            print(f"#{item['rank']} {item['model_identifier']} → {item['score']} points")
        
        # 2. Get user models
        print("\n=== User Models ===")
        user_keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        if user_keys:
            test_user_id = user_keys[0].user_id
            user_models = get_user_models_by_tier(db, test_user_id)
            
            for tier, models in user_models.items():
                if models:
                    print(f"\n{tier}: {len(models)} models")
                    for model in models:
                        print(f"  - {model.get('model_path', 'NO_PATH')}")
        
        # 3. Test router with user models
        print("\n=== Testing Router with User Models ===")
        router = LangGraphRouter(
            models_config={
                "tier1": [m[1] for m in MODELS_CONFIG["tier1"]],
                "tier2": [m[1] for m in MODELS_CONFIG["tier2"]],
                "tier3": [m[1] for m in MODELS_CONFIG["tier3"]],
            },
            cache=None,
            classifier=None,
            llm_client=None,
            db_session=db
        )
        
        # Simulate a query with user models
        if user_keys:
            test_user_id = user_keys[0].user_id
            user_models = get_user_models_by_tier(db, test_user_id)
            
            # This should update the LLMClient with user models
            router._update_llm_client_with_user_models(user_models)
            
            # Check the fallback handler models
            print("\n=== Fallback Handler Models After Update ===")
            if hasattr(router.llm_client, 'fallback_handlers'):
                tier2_handler = router.llm_client.fallback_handlers.get('tier2')
                if tier2_handler:
                    print(f"Tier2 has {len(tier2_handler.models)} models:")
                    for i, model in enumerate(tier2_handler.models, 1):
                        if isinstance(model, (list, tuple)) and len(model) >= 2:
                            print(f"  #{i} {model[0]} → {model[1]}")
                        else:
                            print(f"  #{i} {model}")
                    
                    # Check if user model is first
                    if tier2_handler.models:
                        first_model = tier2_handler.models[0]
                        if isinstance(first_model, (list, tuple)) and len(first_model) >= 2:
                            first_model_id = first_model[1]
                        else:
                            first_model_id = first_model
                        
                        # Check if this is a user model
                        is_user_model = False
                        for tier, models in user_models.items():
                            for model in models:
                                if model.get('model_path') == first_model_id:
                                    is_user_model = True
                                    break
                        
                        if is_user_model:
                            print(f"\n✅ SUCCESS: User model {first_model_id} is first in fallback chain!")
                        else:
                            print(f"\n❌ FAILED: First model {first_model_id} is not a user model")
        
        db.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_model_priority_fix()
