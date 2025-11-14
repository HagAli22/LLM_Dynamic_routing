"""Test script for new model rating feature"""

from database import get_db, ModelRating
from model_rating_system import ModelRatingManager
from crud import _initialize_user_model_rating

def test_new_model_rating():
    """Test that new models get same rating as top model in tier"""
    
    db = next(get_db())
    
    try:
        # 1. Show current tier1 models
        print("=== Current Tier1 Models ===")
        tier1_models = db.query(ModelRating).filter(
            ModelRating.tier == "tier1"
        ).order_by(ModelRating.score.desc()).all()
        
        for i, model in enumerate(tier1_models, 1):
            print(f"#{i} {model.model_identifier} → {model.score} points")
        
        if tier1_models:
            top_score = tier1_models[0].score
            print(f"\nTop model score: {top_score}")
            
            # 2. Test adding new model
            new_model_name = "test-custom-model"
            print(f"\n=== Adding new model: {new_model_name} ===")
            
            # Clean up if exists
            existing = db.query(ModelRating).filter(
                ModelRating.model_identifier == new_model_name
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
            
            # Add new model
            _initialize_user_model_rating(db, new_model_name, "tier1")
            
            # 3. Show updated tier1 models
            print("\n=== Updated Tier1 Models ===")
            updated_models = db.query(ModelRating).filter(
                ModelRating.tier == "tier1"
            ).order_by(ModelRating.score.desc()).all()
            
            for i, model in enumerate(updated_models, 1):
                print(f"#{i} {model.model_identifier} → {model.score} points")
            
            # 4. Verify new model has same score as top model
            new_model = db.query(ModelRating).filter(
                ModelRating.model_identifier == new_model_name
            ).first()
            
            if new_model and new_model.score == top_score:
                print(f"\n✅ SUCCESS: {new_model_name} started with {new_model.score} points (same as top model)")
            else:
                print(f"\n❌ FAILED: {new_model_name} has {new_model.score} points (expected {top_score})")
            
            # Clean up test model
            if new_model:
                db.delete(new_model)
                db.commit()
                print(f"🧹 Cleaned up test model: {new_model_name}")
        
        else:
            print("\n❌ No models found in tier1")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_new_model_rating()
