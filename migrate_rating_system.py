"""
Migration Script for Model Rating System
تشغيل هذا السكريبت لإضافة جداول نظام التقييم
"""

from database import init_db, SessionLocal
from config import MODELS_CONFIG
from database import ModelRating
import sys

def migrate():
    """تشغيل الـ migration"""
    print("="*60)
    print("🔄 Starting Model Rating System Migration")
    print("="*60)
    
    try:
        # إنشاء الجداول
        print("\n1️⃣ Creating database tables...")
        init_db()
        
        # تهيئة نقاط الموديلات
        print("\n2️⃣ Initializing model ratings...")
        db = SessionLocal()
        
        total_models = 0
        for tier, models in MODELS_CONFIG.items():
            print(f"\n   Processing {tier}...")
            for model in models:
                if isinstance(model, (list, tuple)) and len(model) >= 2:
                    model_name = model[0]
                    model_identifier = model[1]
                else:
                    model_name = model
                    model_identifier = model
                
                # التحقق من وجود الموديل
                existing = db.query(ModelRating).filter(
                    ModelRating.model_identifier == model_identifier
                ).first()
                
                if not existing:
                    new_rating = ModelRating(
                        model_identifier=model_identifier,
                        model_name=model_name,
                        tier=tier,
                        score=100  # النقاط الابتدائية
                    )
                    db.add(new_rating)
                    print(f"   ✅ Added: {model_name} ({tier})")
                    total_models += 1
                else:
                    print(f"   ⏭️  Skipped (exists): {model_name}")
        
        db.commit()
        db.close()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   Total new models added: {total_models}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("="*60)
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
