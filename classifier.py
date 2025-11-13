"""
Text Classification Module - Simplified Version
Uses basic heuristics for demo. Replace with your trained model when available.
"""
import os

# Try to load custom model if available
# Default to local best_model if exists
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "best_model")
MODEL_PATH = os.getenv("CLASSIFIER_MODEL_PATH", DEFAULT_MODEL_PATH if os.path.exists(DEFAULT_MODEL_PATH) else None)
pipe = None

if MODEL_PATH and os.path.exists(MODEL_PATH):
    try:
        import torch
        from transformers import pipeline
        pipe = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH, 
                       device=0 if torch.cuda.is_available() else -1)
        print("✅ Custom classifier model loaded successfully!")
    except Exception as e:
        print(f"⚠️  Could not load custom model: {e}")
        print("   Using fallback heuristic classifier...")


def classify_text(text):
    """
    Classify text into S (Simple), M (Medium), or A (Advanced)
    
    If custom model is available, use it. Otherwise use heuristics.
    Returns: "S" for Simple, "M" for Medium, "A" for Advanced
    """
    if pipe is not None:
        try:
            pred = pipe(text)[0]
            label = pred['label']
            # Map model output to S/M/A format
            if label in ['Simple', 'S']:
                return 'S'
            elif label in ['Moderate', 'Medium', 'M']:
                return 'M'
            elif label in ['Complex', 'Advanced', 'A']:
                return 'A'
            return label
        except Exception as e:
            print(f"⚠️  Model prediction failed: {e}, using fallback...")
    
    # Fallback: Simple heuristic-based classification
    text_lower = text.lower()
    word_count = len(text.split())
    
    # Advanced/Complex indicators
    complex_words = ['quantum', 'algorithm', 'complex', 'advanced', 'sophisticated', 
                     'multi-step', 'comprehensive', 'intricate', 'theoretical', 'develop',
                     'design', 'architecture', 'implement', 'optimize', 'analyze']
    
    # Simple indicators
    simple_words = ['what', 'who', 'when', 'where', 'define', 'explain', 'simple',
                   'is', 'are', 'capital', 'name', 'basic']
    
    # Coding/technical indicators
    code_words = ['code', 'function', 'program', 'script', 'application', 'api']
    
    complex_score = sum(1 for word in complex_words if word in text_lower)
    simple_score = sum(1 for word in simple_words if word in text_lower)
    code_score = sum(1 for word in code_words if word in text_lower)
    
    # Classification logic - returns S, M, or A
    if complex_score >= 2 or word_count > 50 or code_score >= 2:
        return "A"  # Advanced
    elif simple_score >= 1 and word_count < 20 and complex_score == 0:
        return "S"  # Simple
    else:
        return "M"  # Medium


# Test examples
if __name__ == "__main__":
    queries = [
        "What is Python?",
        "Explain machine learning concepts.",
        "Develop a multi-step plan to reduce carbon emissions considering economic factors.",
        "What is the capital of France?",
        "Create code for a weather application"
    ]
    
    classification_names = {
        "S": "Simple (Tier 1)",
        "M": "Medium (Tier 2)", 
        "A": "Advanced (Tier 3)"
    }
    
    print("="*60)
    print("🧪 Testing Classifier")
    print("="*60 + "\n")
    
    for q in queries:
        result = classify_text(q)
        print(f"🔹 Query: {q}")
        print(f"   → Classification: {result} - {classification_names.get(result, 'Unknown')}\n")
