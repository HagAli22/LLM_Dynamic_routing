"""
اختبار سريع لنظام التقييم
"""

from database import SessionLocal, ModelRating
from model_rating_system import ModelRatingManager

def test_rating():
    db = SessionLocal()
    manager = ModelRatingManager(db)
    
    # الموديل اللي اتقيم
    model_id = "meta-llama/llama-3.3-8b-instruct:free"
    
    print("="*60)
    print("🔍 فحص نقاط الموديل")
    print("="*60)
    
    # البحث عن الموديل
    model = db.query(ModelRating).filter(
        ModelRating.model_identifier == model_id
    ).first()
    
    if model:
        print(f"\n✅ الموديل موجود!")
        print(f"   الاسم: {model.model_name}")
        print(f"   Tier: {model.tier}")
        print(f"   النقاط: {model.score}")
        print(f"   👍 Likes: {model.total_likes}")
        print(f"   👎 Dislikes: {model.total_dislikes}")
        print(f"   ⭐ Stars: {model.total_stars}")
        print(f"   إجمالي التقييمات: {model.total_feedbacks}")
    else:
        print(f"\n❌ الموديل غير موجود في قاعدة البيانات!")
        print(f"   جاري إنشاء سجل جديد...")
        
        # إضافة تقييم تجريبي
        result = manager.add_feedback(
            query_id=1,
            user_id=1,
            model_identifier=model_id,
            feedback_type='star',
            comment='Test rating'
        )
        print(f"\n✅ تم إنشاء السجل: {result}")
    
    # عرض الترتيب في tier1
    print(f"\n\n📊 ترتيب Tier 1:")
    print("="*60)
    
    leaderboard = manager.get_tier_leaderboard('tier1', limit=5)
    for item in leaderboard:
        print(f"\n#{item['rank']} {item['model_name']}")
        print(f"   النقاط: {item['score']}")
        print(f"   👍 {item['total_likes']} | 👎 {item['total_dislikes']} | ⭐ {item['total_stars']}")
    
    db.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    test_rating()
