"""Debug model identifiers in database and routing"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_model_identifiers():
    """Debug what model identifiers are stored and used"""
    
    print("🔍 Debugging model identifiers...")
    
    try:
        from database import get_db, ModelRating, UserAPIKey
        from model_rating_system import ModelRatingManager
        from langgraph_router import LangGraphRouter
        from crud import get_user_models_by_tier
        
        db = next(get_db())
        
        # 1. Check model ratings table
        print("\n=== Model Ratings Table ===")
        all_ratings = db.query(ModelRating).all()
        
        for rating in all_ratings:
            print(f"ID: {rating.model_identifier} | Name: {rating.model_name} | Tier: {rating.tier}")
        
        # 2. Check user API keys table
        print("\n=== User API Keys Table ===")
        user_keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        for key in user_keys:
            print(f"Name: {key.model_name} | Path: {key.model_path} | Tier: {key.tier}")
        
        # 3. Check ranking system
        print("\n=== Ranking System ===")
        manager = ModelRatingManager(db)
        
        for tier in ['tier1', 'tier2', 'tier3']:
            leaderboard = manager.get_tier_leaderboard(tier, limit=3)
            if leaderboard:
                print(f"\n{tier}:")
                for item in leaderboard:
                    print(f"  #{item['rank']} {item['model_identifier']}")
        
        # 4. Check user models from crud
        print("\n=== User Models from CRUD ===")
        if user_keys:
            test_user_id = user_keys[0].user_id
            user_models = get_user_models_by_tier(db, test_user_id)
            
            for tier, models in user_models.items():
                if models:
                    print(f"\n{tier}:")
                    for model in models:
                        print(f"  model_path: {model.get('model_path')}")
                        print(f"  env_var_name: {model.get('env_var_name')}")
        
        # 5. Check router models config
        print("\n=== Router Models Config ===")
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
        
        for tier, models in router.models_config.items():
            print(f"\n{tier}: {len(models)} models")
            for model in models[:3]:  # Show first 3
                print(f"  {model}")
        
        db.close()
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model_identifiers()
