"""
Simple Router for Streamlit Cloud deployment (no langgraph dependency)
"""
import logging
from typing import Optional, Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_RETRIES_PER_MODEL = 3


class SimpleRouter:
    """
    Simplified router without LangGraph dependency.
    Handles query classification, model selection, caching, and retries.
    """

    def __init__(
        self,
        models_config: dict,
        cache,
        classifier,
        llm_client=None,
        max_retries: int = MAX_RETRIES_PER_MODEL,
    ):
        self.models_config = models_config
        self.cache = cache
        self.classifier = classifier
        self.llm_client = llm_client
        self.max_retries = max_retries

    def _map_classification_to_tier(self, classification: str) -> str:
        """Map classification letter to tier key."""
        mapping = {"S": "tier1", "M": "tier2", "A": "tier3"}
        return mapping.get(classification, "tier1")

    def route(self, query: str) -> Dict[str, Any]:
        """Run a query through the routing logic."""
        state = {
            "query": query,
            "classification": None,
            "model_tier": None,
            "selected_model": None,
            "cache_hit": False,
            "cached_response": None,
            "llm_response": None,
            "used_model": None,
            "error": None,
            "retry_count": 0,
        }

        # Step 1: Check cache
        try:
            cached = self.cache.get(query)
            if cached:
                state["cache_hit"] = True
                state["cached_response"] = cached
                state["llm_response"] = cached
                return state
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        # Step 2: Classify query
        try:
            classification = self.classifier.classify_text(query)
            if classification not in ["S", "M", "A"]:
                classification = "S"
            state["classification"] = classification
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state["classification"] = "S"

        # Step 3: Select model and call LLM with retries
        tier_key = self._map_classification_to_tier(state["classification"])
        state["model_tier"] = tier_key
        models = self.models_config.get(tier_key, [])

        if not models:
            state["error"] = f"No models available for {tier_key}"
            return state

        max_attempts = len(models) * self.max_retries
        
        for attempt in range(max_attempts):
            model_idx = attempt % len(models)
            selected_model = models[model_idx]
            
            if isinstance(selected_model, (list, tuple)) and len(selected_model) > 1:
                selected_model = selected_model[1]
            
            state["selected_model"] = selected_model
            state["retry_count"] = attempt + 1

            try:
                if self.llm_client:
                    result = self.llm_client.call(
                        selected_model,
                        [{"role": "user", "content": query}],
                        tier_key,
                    )
                    
                    if isinstance(result, dict):
                        state["llm_response"] = result
                        state["used_model"] = result.get("model", selected_model)
                    else:
                        state["llm_response"] = result
                        state["used_model"] = selected_model
                    
                    # Store in cache
                    try:
                        self.cache.set(query, state["llm_response"])
                    except:
                        pass
                    
                    return state
                else:
                    # Mock response
                    state["llm_response"] = f"Response for: {query}"
                    state["used_model"] = selected_model
                    return state

            except Exception as e:
                logger.warning(f"Model {selected_model} failed (attempt {attempt + 1}): {e}")
                state["error"] = str(e)
                continue

        return state
