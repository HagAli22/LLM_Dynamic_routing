"""
اختبار API endpoint للتقييم
"""

import requests
import json

# تسجيل الدخول أولاً
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "your_username",  # غير ده باسم المستخدم بتاعك
    "password": "your_password"   # غير ده بالباسورد بتاعك
}

print("="*60)
print("🔐 تسجيل الدخول...")
print("="*60)

try:
    # تسجيل الدخول
    response = requests.post(
        login_url,
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ تم تسجيل الدخول بنجاح!")
        print(f"Token: {token[:20]}...")
        
        # إرسال تقييم
        print("\n" + "="*60)
        print("⭐ إرسال تقييم...")
        print("="*60)
        
        feedback_url = "http://localhost:8000/api/rating/feedback"
        feedback_data = {
            "query_id": 1,  # استخدم query_id حقيقي من قاعدة البيانات
            "model_identifier": "meta-llama/llama-3.3-8b-instruct:free",
            "feedback_type": "star",
            "comment": "Test from API"
        }
        
        response = requests.post(
            feedback_url,
            json=feedback_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ التقييم تم بنجاح!")
            
            # التحقق من النقاط
            print("\n" + "="*60)
            print("🔍 التحقق من النقاط...")
            print("="*60)
            
            from database import SessionLocal, ModelRating
            db = SessionLocal()
            model = db.query(ModelRating).filter(
                ModelRating.model_identifier == "meta-llama/llama-3.3-8b-instruct:free"
            ).first()
            
            if model:
                print(f"\n✅ النقاط الحالية: {model.score}")
                print(f"   ⭐ Stars: {model.total_stars}")
                print(f"   👍 Likes: {model.total_likes}")
                print(f"   👎 Dislikes: {model.total_dislikes}")
            
            db.close()
        else:
            print(f"\n❌ فشل التقييم!")
            print(f"Error: {response.text}")
    
    else:
        print(f"❌ فشل تسجيل الدخول!")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ خطأ: {e}")

print("\n" + "="*60)
