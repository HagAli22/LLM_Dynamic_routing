"""Check if API keys are configured"""

from dotenv import load_dotenv
import os

load_dotenv()

print("="*60)
print("🔑 Checking API Keys")
print("="*60)

openrouter = os.getenv("OPENROUTER_API_KEY")
openai = os.getenv("OPENAI_API_KEY")

print(f"\n✅ OPENROUTER_API_KEY: {'SET (' + openrouter[:20] + '...)' if openrouter else '❌ NOT SET'}")
print(f"✅ OPENAI_API_KEY: {'SET (' + openai[:20] + '...)' if openai else '❌ NOT SET'}")

if openrouter or openai:
    print("\n✅ At least one API key is configured!")
    print("\n📝 Testing API connection...")
    
    import requests
    
    api_key = openrouter or openai
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API connection works!")
            result = response.json()
            print(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Message: {response.text}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
else:
    print("\n❌ No API keys found!")
    print("Please check your .env file and make sure OPENROUTER_API_KEY or OPENAI_API_KEY is set")
