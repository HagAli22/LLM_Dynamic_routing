"""Initialize database and test new model rating feature"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_and_test():
    """Initialize database and test the feature"""
    
    print("🔧 Initializing database...")
    
    try:
        # Import and initialize database
        from database import init_db, get_db, ModelRating
        
        # Initialize database tables
        init_db()
        
        print("\n📊 Database initialized! Testing new model rating feature...")
        
        # Now test the feature
        db = next(get_db())
        
        # 1. Show current tier1 models
        print("\n=== Current Tier1 Models ===")
        tier1_models = db.query(ModelRating).filter(
            ModelRating.tier == "tier1"
        ).order_by(ModelRating.score.desc()).all()
        
        for i, model in enumerate(tier1_models, 1):
            print(f"#{i} {model.model_identifier} → {model.score} points")
        
        if tier1_models:
            top_score = tier1_models[0].score
            print(f"\n🏆 Top model score: {top_score}")
            
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
            
            # Add new model using the feature
            from crud import _initialize_user_model_rating
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
            print("\n❌ No models found in tier1 - this is normal for first run!")
            print("The system will create default models with 100 points each.")
        
        db.close()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    initialize_and_test()
