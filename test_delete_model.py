"""Test that deleted models are removed from ranking"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_delete_model():
    """Test that deleted models are removed from ranking"""
    
    print("🗑️ Testing model deletion from ranking...")
    
    try:
        from database import init_db, get_db, ModelRating, UserAPIKey
        from crud import _initialize_user_model_rating, delete_user_api_key
        
        # Initialize database
        init_db()
        
        db = next(get_db())
        
        # 1. Show current models
        print("\n=== Current Models in Rating ===")
        all_models = db.query(ModelRating).order_by(ModelRating.score.desc()).all()
        
        for i, model in enumerate(all_models, 1):
            print(f"#{i} {model.model_identifier} → {model.score} points")
        
        # 2. Add a test model
        test_model = "test-delete-model"
        print(f"\n=== Adding test model: {test_model} ===")
        
        # Clean up if exists
        existing = db.query(ModelRating).filter(
            ModelRating.model_identifier == test_model
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
        
        # Add test model
        _initialize_user_model_rating(db, test_model, "tier1")
        
        # Verify it was added
        test_rating = db.query(ModelRating).filter(
            ModelRating.model_identifier == test_model
        ).first()
        
        if test_rating:
            print(f"✅ Model added: {test_rating.model_identifier} → {test_rating.score} points")
        
        # 3. Show updated ranking
        print("\n=== Ranking After Adding Test Model ===")
        updated_models = db.query(ModelRating).order_by(ModelRating.score.desc()).all()
        
        for i, model in enumerate(updated_models, 1):
            if model.model_identifier == test_model:
                print(f"#{i} {model.model_identifier} → {model.score} points 🆕")
            else:
                print(f"#{i} {model.model_identifier} → {model.score} points")
        
        # 4. Delete the model (simulate API key deletion)
        print(f"\n=== Deleting test model: {test_model} ===")
        
        # Create a fake API key record to delete
        fake_key = UserAPIKey(
            user_id=1,
            provider="test",
            encrypted_key="test",
            key_name="test",
            model_name=test_model,
            tier="tier1"
        )
        db.add(fake_key)
        db.commit()
        
        # Delete it (this should also remove from rating)
        delete_user_api_key(db, fake_key.id, 1)
        
        # 5. Verify model is gone from ranking
        print("\n=== Final Ranking After Deletion ===")
        final_models = db.query(ModelRating).order_by(ModelRating.score.desc()).all()
        
        test_still_exists = False
        for i, model in enumerate(final_models, 1):
            if model.model_identifier == test_model:
                print(f"#{i} {model.model_identifier} → {model.score} points ❌ STILL EXISTS!")
                test_still_exists = True
            else:
                print(f"#{i} {model.model_identifier} → {model.score} points")
        
        if not test_still_exists:
            print(f"\n✅ SUCCESS: {test_model} was completely removed from ranking!")
        else:
            print(f"\n❌ FAILED: {test_model} is still in ranking system")
        
        db.close()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delete_model()
