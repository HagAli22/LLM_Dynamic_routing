"""Prompt Improvement System - اقتراح برومبتات أوضح"""

from typing import List, Dict
import re


class PromptImprover:
    """Suggest better prompts when user input is unclear"""
    
    def __init__(self):
        # قواعد الكشف عن البرومبتات الغير واضحة
        self.unclear_patterns = [
            r'^.{1,10}$',  # Very short prompts
            r'^(hi|hello|hey|السلام|مرحبا|هاي)$',  # Greetings only
            r'^(what|how|why|ايه|ازاي|ليه)\?*$',  # Single question words
        ]
    
    def is_unclear(self, prompt: str) -> bool:
        """Check if prompt is unclear/vague"""
        prompt = prompt.strip().lower()
        
        # Check length
        if len(prompt) < 10:
            return True
        
        # Check patterns
        for pattern in self.unclear_patterns:
            if re.match(pattern, prompt, re.IGNORECASE):
                return True
        
        # Check if it's just one or two words
        words = prompt.split()
        if len(words) <= 2:
            return True
        
        return False
    
    def generate_suggestions(self, prompt: str) -> Dict[str, any]:
        """Generate clearer prompt suggestions"""
        
        if not self.is_unclear(prompt):
            return {
                "is_clear": True,
                "original_prompt": prompt,
                "suggestions": [],
                "explanation": "Your prompt is clear and specific."
            }
        
        suggestions = self._create_suggestions(prompt)
        
        return {
            "is_clear": False,
            "original_prompt": prompt,
            "suggestions": suggestions,
            "explanation": "Your prompt might be too vague. Here are clearer alternatives:"
        }
    
    def _create_suggestions(self, prompt: str) -> List[str]:
        """Create specific suggestions based on prompt"""
        prompt_lower = prompt.lower().strip()
        
        # Greeting responses
        if re.match(r'^(hi|hello|hey|السلام|مرحبا|هاي)', prompt_lower):
            return [
                "Hello! I need help with [specific topic]",
                "Can you explain [concept] to me?",
                "I want to learn about [subject]"
            ]
        
        # Single question words
        if prompt_lower in ['what', 'ايه', 'إيه']:
            return [
                "What is [specific concept or term]?",
                "What are the main features of [topic]?",
                "What is the difference between [X] and [Y]?"
            ]
        
        if prompt_lower in ['how', 'ازاي', 'إزاي']:
            return [
                "How do I [accomplish specific task]?",
                "How does [system/concept] work?",
                "How can I improve [specific skill]?"
            ]
        
        if prompt_lower in ['why', 'ليه', 'ليه']:
            return [
                "Why is [concept] important?",
                "Why does [phenomenon] happen?",
                "Why should I use [tool/method]?"
            ]
        
        # Very short prompts
        if len(prompt.split()) <= 2:
            return [
                f"Explain {prompt} in detail",
                f"What are the main concepts of {prompt}?",
                f"How do I use {prompt} effectively?",
                f"Give me examples of {prompt}"
            ]
        
        # Default suggestions
        return [
            f"Can you explain {prompt} in more detail?",
            f"What are the key aspects of {prompt}?",
            f"Provide a comprehensive overview of {prompt}",
            f"Give me practical examples related to {prompt}"
        ]
    
    def suggest_by_intent(self, prompt: str, intent: str = None) -> List[str]:
        """Suggest prompts based on detected intent"""
        
        suggestions_by_intent = {
            "learning": [
                f"Teach me about {prompt} step by step",
                f"Explain {prompt} like I'm a beginner",
                f"What are the fundamentals of {prompt}?"
            ],
            "coding": [
                f"Write a Python code example for {prompt}",
                f"Show me best practices for {prompt}",
                f"Debug this code: {prompt}"
            ],
            "comparison": [
                f"Compare and contrast {prompt}",
                f"What are the pros and cons of {prompt}?",
                f"Which is better: {prompt}?"
            ],
            "definition": [
                f"Define {prompt} with examples",
                f"What does {prompt} mean in simple terms?",
                f"Explain {prompt} and its applications"
            ]
        }
        
        if intent and intent in suggestions_by_intent:
            return suggestions_by_intent[intent]
        
        return self.generate_suggestions(prompt)["suggestions"]


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    improver = PromptImprover()
    
    # Test cases
    test_prompts = [
        "hi",
        "what",
        "Python",
        "How do I learn machine learning effectively?"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Original: {prompt}")
        result = improver.generate_suggestions(prompt)
        
        if result["is_clear"]:
            print("✅ Clear prompt")
        else:
            print("⚠️ Unclear prompt")
            print("\nSuggestions:")
            for i, suggestion in enumerate(result["suggestions"], 1):
                print(f"  {i}. {suggestion}")
