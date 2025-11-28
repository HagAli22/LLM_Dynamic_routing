import os
import time
import requests

# Load env vars - graceful fallback for Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to load from Streamlit secrets
def get_secret(key, default=None):
    """Get secret from Streamlit or environment"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)

# Map models to environment variable names
MODEL_KEY_MAP = {
    "mistralai/mistral-7b-instruct:free": "mistral-7b-instruct",
    "qwen/qwen2.5-vl-32b-instruct:free": "qwen2.5-vl-32b-instruct",
    "meta-llama/llama-3.3-8b-instruct:free": "llama-3.3-8b-instruct",
    "qwen/qwen-2.5-72b-instruct:free": "qwen-2.5-72b-instruct",
    "openai/gpt-oss-20b:free": "gpt-oss-20b",
    "mistralai/devstral-small-2505:free": "devstral-small-2505",
    "qwen/qwq-32b:free": "qwq-32b",
    "qwen/qwen-2.5-coder-32b-instruct:free": "qwen-2.5-coder-32b-instruct",
    "deepseek/deepseek-r1-distill-llama-70b:free": "deepseek-r1-distill-llama-70b",
    "meta-llama/llama-3.3-70b-instruct:free": "llama-3.3-70b-instruct",
}

# Price per 1M tokens
PRICES = {
    "qwen-2.5-72b-instruct": {"input": 0.7, "output": 0.7},
    "mistral-7b-instruct": {"input": 0.25, "output": 0.25},
    "llama-3.3-8b-instruct": {"input": 0.15, "output": 0.15},
    "qwen/qwen2.5-vl-32b-instruct:free": {"input": 0.15, "output": 0.15},
    "openai/gpt-oss-20b:free": {"input": 0.15, "output": 0.15},
    "mistralai/devstral-small-2505:free": {"input": 0.15, "output": 0.15},
    "qwen/qwq-32b:free": {"input": 0.15, "output": 0.15},
    "qwen/qwen-2.5-coder-32b-instruct:free": {"input": 0.15, "output": 0.15},
    "deepseek/deepseek-r1-distill-llama-70b:free": {"input": 0.15, "output": 0.15},
    "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.15, "output": 0.15},
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calc cost based on token usage"""
    if model_name not in PRICES:
        return 0.0
    # add try and expcept for price = PRICES[model_name]

    try:
        price = PRICES[model_name]
    except KeyError:
        price =PRICES['deepseek/deepseek-r1-distill-llama-70b:free']
        
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000


class FallbackChatGradientAI:
    """Try multiple models until success"""

    def __init__(self, models: list[str], user_api_keys: dict = None):
        """
        Initialize fallback system
        
        Args:
            models: List of model paths to try
            user_api_keys: Dict mapping model_path -> api_key for user's custom models
        """
        self.models = models
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.user_api_keys = user_api_keys or {}
        
        # Load model-specific API keys from environment
        self._load_env_api_keys()
    
    def _load_env_api_keys(self):
        """
        Load model-specific API keys from environment variables.
        Maps model identifiers to their corresponding API keys from .env
        """
        # Mapping of model patterns to environment variable names
        env_key_mappings = {
            "mistralai/": "MISTRAL_API_KEY",
            "qwen/": "QWEN_API_KEY",
            "meta-llama/": "LLAMA_API_KEY",
            "deepseek/": "DEEPSEEK_API_KEY",
            "openai/gpt-oss": "GPT_API_KEY",
        }
        
        # Check each model and try to find a specific API key
        for model in self.models:
            # Handle model format (can be tuple or string)
            if isinstance(model, (list, tuple)) and len(model) > 1:
                model_identifier = model[1]
            else:
                model_identifier = model
            
            # Skip if already has a custom key
            if model_identifier in self.user_api_keys:
                continue
            
            # Try to find API key from MODEL_KEY_MAP
            api_key_name = MODEL_KEY_MAP.get(model_identifier)
            if api_key_name:
                api_key = os.getenv(api_key_name)
                if api_key:
                    self.user_api_keys[model_identifier] = api_key
                    print(f"✅ Loaded API key for {model_identifier} from {api_key_name}")
            
            # Fallback: Try to find a matching environment variable by pattern
            if model_identifier not in self.user_api_keys:
                for pattern, env_var in env_key_mappings.items():
                    if pattern in model_identifier:
                        api_key = os.getenv(env_var)
                        if api_key:
                            self.user_api_keys[model_identifier] = api_key
                            print(f"✅ Loaded API key for {model_identifier} from {env_var}")
                            # break

    def invoke(self, prompt: str, max_retries: int = 3):
        """
        Send prompt to models with fallback mechanism.
        
        Args:
            prompt: The query text to send
            max_retries: Maximum retry attempts per model
            
        Returns:
            Dict with model, response, tokens, cost, and time_taken
            
        Raises:
            Exception: If all models fail after all retries
        """
        last_exception = None
        
        # Default system API key - check Streamlit secrets first
        default_api_key = get_secret("OPENROUTER_API_KEY") or get_secret("OPENAI_API_KEY")

        print(f"\n🔄 Starting fallback chain with {len(self.models)} models...")
        
        for model_idx, model_name in enumerate(self.models, 1):
            # Handle model format (can be tuple or string)
            if isinstance(model_name, (list, tuple)) and len(model_name) > 1:
                model_display_name = model_name[0]
                model_identifier = model_name[1]
            else:
                model_display_name = model_name
                model_identifier = model_name
            
            # Check if user has custom API key for this model
            print('model_identifier', model_identifier)
            api_key = self.user_api_keys.get(model_identifier, default_api_key)
            print('api_key', api_key)
            
            if not api_key:
                print(f"⚠️ Skipping {model_display_name} - no API key")
                continue
            
            print(f"\n📡 Trying model {model_idx}/{len(self.models)}: {model_identifier}")
            if model_identifier in self.user_api_keys:
                print(f"   🔑 Using user's custom API key")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_identifier,  # This should be the full path like deepseek/deepseek-chat-v3.1:free
                "messages": [{"role": "user", "content": prompt}],
            }
            
            for attempt in range(2):
                try:
                    print(f"   ⏳ Attempt {attempt + 1}/{max_retries}...", end=" ")
                    start_time = time.time()
                    
                    # Add 30 second timeout to prevent hanging
                    response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)

                    if response.status_code == 200:
                        result = response.json()
                        choice = result["choices"][0]["message"]["content"]

                        usage = result.get("usage", {})
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)

                        cost = calculate_cost(model_identifier, input_tokens, output_tokens)
                        end_time = time.time()
                        
                        print(f"✅ Success! ({end_time - start_time:.2f}s)")

                        return {
                            "model": model_identifier,
                            "model_display_name": model_display_name,
                            "response": choice,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost": cost,
                            "time_taken": end_time - start_time,
                        }

                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                        print(f"❌ Failed - {error_msg}")
                        last_exception = Exception(error_msg)
                        time.sleep(1)  # Brief delay before retry

                except requests.exceptions.Timeout:
                    print(f"⏱️ Timeout")
                    last_exception = Exception("Request timeout (30s)")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)[:50]}")
                    last_exception = e
                    time.sleep(1)

        error_msg = f"All {len(self.models)} models failed after {max_retries} retries each. Last error: {str(last_exception)}"
        print(f"\n💥 {error_msg}")
        raise Exception(error_msg)
