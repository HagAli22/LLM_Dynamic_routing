"""Test that new models appear as #1 in ranking"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_new_model_first():
    """Test that new models become #1 in ranking"""
    
    print("🏆 Testing new model as #1 in ranking...")
    
    try:
        from database import init_db, get_db, ModelRating
        from crud import _initialize_user_model_rating
        
        # Initialize database
        init_db()
        
        db = next(get_db())
        
        # 1. Show current tier1 models
        print("\n=== Current Tier1 Models ===")
        tier1_models = db.query(ModelRating).filter(
            ModelRating.tier == "tier1"
        ).order_by(ModelRating.score.desc()).all()
        
        for i, model in enumerate(tier1_models, 1):
            print(f"#{i} {model.model_identifier} → {model.score} points")
        
        if tier1_models:
            old_top_score = tier1_models[0].score
            old_top_name = tier1_models[0].model_identifier
            print(f"\n👑 Old #1: {old_top_name} → {old_top_score} points")
            
            # 2. Add new model
            new_model_name = "test-new-first-model"
            print(f"\n=== Adding new model: {new_model_name} ===")
            
            # Clean up if exists
            existing = db.query(ModelRating).filter(
                ModelRating.model_identifier == new_model_name
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
            
            # Add new model - should become #1
            _initialize_user_model_rating(db, new_model_name, "tier1")
            
            # 3. Show updated ranking
            print("\n=== Updated Tier1 Models ===")
            updated_models = db.query(ModelRating).filter(
                ModelRating.tier == "tier1"
            ).order_by(ModelRating.score.desc()).all()
            
            for i, model in enumerate(updated_models, 1):
                print(f"#{i} {model.model_identifier} → {model.score} points")
            
            # 4. Verify new model is #1
            new_model = db.query(ModelRating).filter(
                ModelRating.model_identifier == new_model_name
            ).first()
            
            if new_model and updated_models[0].model_identifier == new_model_name:
                print(f"\n✅ SUCCESS: {new_model_name} is now #1 with {new_model.score} points!")
                print(f"   Previous #1 ({old_top_name}) is now #2 with {old_top_score} points")
            else:
                print(f"\n❌ FAILED: {new_model_name} is not #1")
            
            # Clean up test model
            if new_model:
                db.delete(new_model)
                db.commit()
                print(f"\n🧹 Cleaned up test model: {new_model_name}")
        
        else:
            print("\n❌ No models found in tier1")
        
        db.close()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_model_first()
