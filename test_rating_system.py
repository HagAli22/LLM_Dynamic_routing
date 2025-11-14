"""
Test Script for Model Rating System
Script to test rating system
"""

from database import SessionLocal
from model_rating_system import ModelRatingManager

def test_rating_system():
    """Test rating system"""
    print("="*60)
    print("🧪 Testing Model Rating System")
    print("="*60)
    
    db = SessionLocal()
    rating_manager = ModelRatingManager(db)
    
    # 1. Show ranked models
    print("\n1️⃣ Current Model Rankings:")
    print("-"*60)
    for tier in ['tier1', 'tier2', 'tier3']:
        print(f"\n{tier.upper()}:")
        models = rating_manager.get_ranked_models(tier)
        for i, model in enumerate(models[:5], 1):  # First 5 models
            stats = rating_manager.get_model_stats(model)
            if stats:
                print(f"  {i}. {stats['model_name']}")
                print(f"     Score: {stats['score']} | Likes: {stats['total_likes']} | Dislikes: {stats['total_dislikes']} | Stars: {stats['total_stars']}")
    
    # 2. Add test ratings
    print("\n\n2️⃣ Adding Test Feedbacks:")
    print("-"*60)
    
    test_model = "qwen/qwen-2.5-72b-instruct:free"
    
    # Add like
    result = rating_manager.add_feedback(
        query_id=1,
        user_id=1,
        model_identifier=test_model,
        feedback_type='like',
        comment='Great response!'
    )
    print(f"\n✅ Added LIKE: {result}")
    
    # Add star
    result = rating_manager.add_feedback(
        query_id=2,
        user_id=1,
        model_identifier=test_model,
        feedback_type='star',
        comment='Excellent!'
    )
    print(f"\n⭐ Added STAR: {result}")
    
    # Add dislike for another model
    test_model2 = "mistralai/mistral-7b-instruct:free"
    result = rating_manager.add_feedback(
        query_id=3,
        user_id=1,
        model_identifier=test_model2,
        feedback_type='dislike',
        comment='Not accurate'
    )
    print(f"\n👎 Added DISLIKE: {result}")
    
    # 3. Show updated statistics
    print("\n\n3️⃣ Updated Statistics:")
    print("-"*60)
    
    stats = rating_manager.get_model_stats(test_model)
    if stats:
        print(f"\nModel: {stats['model_name']}")
        print(f"Score: {stats['score']}")
        print(f"Total Feedbacks: {stats['total_feedbacks']}")
        print(f"Likes: {stats['total_likes']} | Dislikes: {stats['total_dislikes']} | Stars: {stats['total_stars']}")
    
    # 4. Show leaderboard
    print("\n\n4️⃣ Leaderboard (Tier 1):")
    print("-"*60)
    
    leaderboard = rating_manager.get_tier_leaderboard('tier1', limit=5)
    for item in leaderboard:
        print(f"\n#{item['rank']} {item['model_name']}")
        print(f"   Score: {item['score']} | Feedbacks: {item['total_feedbacks']}")
        print(f"   👍 {item['total_likes']} | 👎 {item['total_dislikes']} | ⭐ {item['total_stars']}")
    
    # 5. Rating history
    print("\n\n5️⃣ Recent Feedback History:")
    print("-"*60)
    
    history = rating_manager.get_feedback_history(limit=5)
    for fb in history:
        print(f"\n{fb['feedback_type'].upper()} ({fb['points_change']:+d} points)")
        print(f"   Model: {fb['model_identifier']}")
        print(f"   Comment: {fb['comment']}")
        print(f"   Time: {fb['created_at']}")
    
    db.close()
    
    print("\n" + "="*60)
    print("✅ Test completed successfully!")
    print("="*60)


if __name__ == "__main__":
    test_rating_system()
