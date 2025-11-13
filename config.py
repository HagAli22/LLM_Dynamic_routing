import os
import sys
from typing import Dict, List
from enum import Enum
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from classifier import classify_text
from fallback import FallbackChatGradientAI
from semantic_cache import SemanticCache

MODELS_CONFIG = {
    "tier1": [
        ["llama-3.3-8b-instruct", "meta-llama/llama-3.3-8b-instruct:free"],
        ["mistral-7b-instruct", "mistralai/mistral-7b-instruct:free"],
        ["qwen2.5-vl-32b-instruct", "qwen/qwen2.5-vl-32b-instruct:free"],
    ],
    "tier2": [
        ["qwen-2.5-72b-instruct", "qwen/qwen-2.5-72b-instruct:free"],
        ["gpt-oss-20b", "openai/gpt-oss-20b:free"],
        ["devstral-small-2505", "mistralai/devstral-small-2505:free"],
    ],
    "tier3": [
        ["qwen-2.5-coder-32b-instruct", "qwen/qwen-2.5-coder-32b-instruct:free"],
        ["deepseek-r1-distill-llama-70b", "deepseek/deepseek-r1-distill-llama-70b:free"],
        ["llama-3.3-70b-instruct", "meta-llama/llama-3.3-70b-instruct:free"],
    ]
}

class Classifier:
    """Wrapper for the classifier to match the expected interface."""
    
    def __init__(self):
        self.classify_text = classify_text

class LLMClient:
    """Wrapper for the LLM client to match the expected interface."""
    
    def __init__(self, models_config: Dict[str, List[List[str]]]):
        self.models_config = models_config
        # Initialize fallback handlers for each tier
        self.fallback_handlers = {
            tier: FallbackChatGradientAI(models=models_list)
            for tier, models_list in models_config.items()
        }
    
    def update_models_config(self, new_models_config: Dict[str, List]):
        """تحديث ترتيب الموديلات ديناميكياً"""
        self.models_config = new_models_config
        # إعادة إنشاء fallback handlers بالترتيب الجديد
        self.fallback_handlers = {
            tier: FallbackChatGradientAI(models=models_list)
            for tier, models_list in new_models_config.items()
        }
    
    def call(self, model: str, messages: List[Dict[str, str]], tier: str):
        """
        Call the LLM with the given messages and force correct tier fallback.
        
        Args:
            model: Model identifier (not used directly, fallback uses tier models)
            messages: List of message dicts with 'role' and 'content'
            tier: Tier name (tier1, tier2, tier3) to select appropriate fallback handler
            
        Returns:
            Dictionary with response details or string response
        """
        # Extract the query (assume one user message)
        query = next((msg["content"] for msg in messages if msg["role"] == "user"), "")

        # Pick the correct fallback handler (default = tier1 if not found)
        fallback = self.fallback_handlers.get(tier, self.fallback_handlers["tier1"])

        # Call the model - returns dict with model, response, tokens, cost, time
        result = fallback.invoke(query)
        
        # Return the full result dict for better tracking
        # The router will extract what it needs
        return result


