"""Check if the new model appears in the ranking system"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_model_ranking():
    """Check if user-added models appear in ranking"""
    
    print("🔍 Checking model ranking system...")
    
    try:
        from database import get_db, ModelRating, UserAPIKey
        from model_rating_system import ModelRatingManager
        
        db = next(get_db())
        
        # 1. Check all models in model_ratings table
        print("\n=== All Models in Rating System ===")
        all_models = db.query(ModelRating).order_by(ModelRating.tier, ModelRating.score.desc()).all()
        
        for model in all_models:
            print(f"{model.tier}: {model.model_identifier} → {model.score} points")
        
        # 2. Check user API keys
        print("\n=== User API Keys ===")
        user_keys = db.query(UserAPIKey).filter(UserAPIKey.is_active == True).all()
        
        for key in user_keys:
            print(f"User {key.user_id}: {key.model_name} ({key.tier})")
            
            # Check if this model exists in rating system
            rating = db.query(ModelRating).filter(
                ModelRating.model_identifier == key.model_name
            ).first()
            
            if rating:
                print(f"  ✅ Found in ranking: {rating.score} points")
            else:
                print(f"  ❌ NOT found in ranking system!")
        
        # 3. Test leaderboard API
        print("\n=== Leaderboard Test ===")
        manager = ModelRatingManager(db)
        
        for tier in ['tier1', 'tier2', 'tier3']:
            leaderboard = manager.get_tier_leaderboard(tier, limit=5)
            if leaderboard:
                print(f"\n{tier.upper()}:")
                for item in leaderboard:
                    print(f"  #{item['rank']} {item['model_identifier']} → {item['score']} points")
            else:
                print(f"\n{tier.upper()}: No models found")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_model_ranking()
