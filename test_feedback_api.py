"""
Test rating API endpoint
"""

import requests
import json

# Login first
login_url = "http://localhost:8000/api/auth/login"
login_data = {
    "username": "your_username",  # Change this to your username
    "password": "your_password"   # Change this to your password
}

print("="*60)
print("🔐 Login...")
print("="*60)

try:
    # Login
    response = requests.post(
        login_url,
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        print(f"Token: {token[:20]}...")
        
        # Send rating
        print("\n" + "="*60)
        print("⭐ Send rating...")
        print("="*60)
        
        feedback_url = "http://localhost:8000/api/rating/feedback"
        feedback_data = {
            "query_id": 1,  # Use real query_id from database
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
            print("\n✅ Rating submitted successfully!")
            
            # Check points
            print("\n" + "="*60)
            print("🔍 Check points...")
            print("="*60)
            
            from database import SessionLocal, ModelRating
            db = SessionLocal()
            model = db.query(ModelRating).filter(
                ModelRating.model_identifier == "meta-llama/llama-3.3-8b-instruct:free"
            ).first()
            
            if model:
                print(f"\n✅ Current points: {model.score}")
                print(f"   ⭐ Stars: {model.total_stars}")
                print(f"   👍 Likes: {model.total_likes}")
                print(f"   👎 Dislikes: {model.total_dislikes}")
            
            db.close()
        else:
            print(f"\n❌ Rating failed!")
            print(f"Error: {response.text}")
    
    else:
        print(f"❌ Login failed!")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60)
