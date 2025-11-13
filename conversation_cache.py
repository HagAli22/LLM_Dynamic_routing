"""
Conversation-based Semantic Cache System
يدعم إنشاء semantic cache منفصل لكل محادثة
"""
import time
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ConversationCache:
    """
    Semantic cache system for individual conversations.
    Each conversation gets its own cache file.
    """

    def __init__(self, conversation_id: int, threshold=0.50, default_ttl=3600):
        self.conversation_id = conversation_id
        self.cache_file = f"cache/conversation_{conversation_id}.json"
        self.threshold = threshold
        self.default_ttl = default_ttl
        
        # Ensure cache directory exists
        os.makedirs("cache", exist_ok=True)
        
        # Load model once (shared across all conversations)
        if not hasattr(ConversationCache, '_model'):
            ConversationCache._model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.model = ConversationCache._model
        self.cache = self._load_cache()

    def _load_cache(self):
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    return [
                        {
                            "embedding": np.array(item["embedding"]),
                            "response": item["response"],
                            "timestamp": item["timestamp"],
                            "ttl": item["ttl"],
                        }
                        for item in raw
                    ]
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_cache(self):
        """Save cache to file"""
        raw = [
            {
                "embedding": emb["embedding"].tolist(),
                "response": emb["response"],
                "timestamp": emb["timestamp"],
                "ttl": emb["ttl"],
            }
            for emb in self.cache
        ]
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(raw, f)

    def _cleanup(self):
        """Remove expired cache entries"""
        now = time.time()
        self.cache = [item for item in self.cache if now - item["timestamp"] <= item["ttl"]]

    def get(self, query: str, threshold: float = None):
        """Retrieve response from cache if query is semantically similar."""
        self._cleanup()

        if not self.cache:
            return None

        query_emb = self.model.encode([query])
        embeddings = np.array([item["embedding"] for item in self.cache])
        sims = cosine_similarity(query_emb, embeddings)[0]

        best_idx = np.argmax(sims)
        best_score = sims[best_idx]
        threshold = threshold if threshold is not None else self.threshold

        if best_score >= threshold:
            return self.cache[best_idx]["response"]
        return None

    def set(self, query: str, response, ttl=None):
        """
        Store query-response pair in cache.
        
        Args:
            query: The query text
            response: The response (can be string or dict with 'response' key)
            ttl: Time to live in seconds (optional)
        """
        # Handle different response formats
        if isinstance(response, dict):
            if 'response' in response:
                response_text = response['response']
            else:
                response_text = str(response)
        else:
            response_text = str(response)
        
        query_emb = self.model.encode([query])[0]
        ttl = ttl if ttl is not None else self.default_ttl
        self.cache.append({
            "embedding": query_emb,
            "response": response_text,
            "timestamp": time.time(),
            "ttl": ttl
        })
        self._save_cache()
        
    def clear(self):
        """Clear all cache entries."""
        self.cache = []
        self._save_cache()
        
    def get_cache_size(self):
        """Get number of cached entries."""
        self._cleanup()
        return len(self.cache)


class CacheManager:
    """
    Manager for multiple conversation caches
    """
    _caches = {}
    
    @classmethod
    def get_cache(cls, conversation_id: int) -> ConversationCache:
        """Get or create cache for a conversation"""
        if conversation_id not in cls._caches:
            cls._caches[conversation_id] = ConversationCache(conversation_id)
        return cls._caches[conversation_id]
    
    @classmethod
    def clear_cache(cls, conversation_id: int):
        """Clear cache for a specific conversation"""
        if conversation_id in cls._caches:
            cls._caches[conversation_id].clear()
            del cls._caches[conversation_id]
    
    @classmethod
    def clear_all_caches(cls):
        """Clear all caches"""
        for cache in cls._caches.values():
            cache.clear()
        cls._caches.clear()
