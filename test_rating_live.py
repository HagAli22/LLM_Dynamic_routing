"""
Quick test for rating system
"""

from database import SessionLocal, ModelRating
from model_rating_system import ModelRatingManager

def test_rating():
    db = SessionLocal()
    manager = ModelRatingManager(db)
    
    # Rated model
    model_id = "meta-llama/llama-3.3-8b-instruct:free"
    
    print("="*60)
    print("🔍 Check model points")
    print("="*60)
    
    # Search for model
    model = db.query(ModelRating).filter(
        ModelRating.model_identifier == model_id
    ).first()
    
    if model:
        print(f"\n✅ Model exists!")
        print(f"   Name: {model.model_name}")
        print(f"   Tier: {model.tier}")
        print(f"   Points: {model.score}")
        print(f"   👍 Likes: {model.total_likes}")
        print(f"   👎 Dislikes: {model.total_dislikes}")
        print(f"   ⭐ Stars: {model.total_stars}")
        print(f"   Total ratings: {model.total_feedbacks}")
    else:
        print(f"\n❌ Model not found in database!")
        print(f"   Creating new record...")
        
        # Add test rating
        result = manager.add_feedback(
            query_id=1,
            user_id=1,
            model_identifier=model_id,
            feedback_type='star',
            comment='Test rating'
        )
        print(f"\n✅ Record created: {result}")
    
    # Show ranking in tier1
    print(f"\n\n📊 Tier 1 Ranking:")
    print("="*60)
    
    leaderboard = manager.get_tier_leaderboard('tier1', limit=5)
    for item in leaderboard:
        print(f"\n#{item['rank']} {item['model_name']}")
        print(f"   Points: {item['score']}")
        print(f"   👍 {item['total_likes']} | 👎 {item['total_dislikes']} | ⭐ {item['total_stars']}")
    
    db.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    test_rating()
