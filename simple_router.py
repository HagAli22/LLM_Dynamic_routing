"""
Simple Router for Streamlit Cloud deployment (no langgraph dependency)
Works exactly like langgraph_router.py but without LangGraph
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
    Same interface as langgraph_router.Router
    """

    def __init__(
        self,
        models_config: dict,
        cache,
        classifier,
        llm_client=None,
        db_session=None,
        max_retries: int = MAX_RETRIES_PER_MODEL,
    ):
        self.models_config = models_config
        self.cache = cache
        self.classifier = classifier
        self.llm_client = llm_client
        self.max_retries = max_retries
        self.db_session = db_session

    def _map_classification_to_tier(self, classification: str) -> str:
        """Map classification letter to tier key."""
        mapping = {"S": "tier1", "M": "tier2", "A": "tier3"}
        return mapping.get(classification, "tier1")

    def check_cache(self, state: dict) -> dict:
        """Check if the query already exists in the semantic cache."""
        logger.debug("Checking cache for query")
        print("DEBUG: Cache check state:")
        try:
            response = self.cache.get(state["query"])
            if response is not None:
                return {
                    **state,
                    "cache_hit": True,
                    "cached_response": response,
                    "llm_response": response,
                }
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
        return {**state, "cache_hit": False}

    def classify_query(self, state: dict) -> dict:
        """Classify the query into Small (S), Medium (M), or Advanced (A)."""
        logger.debug("Classifying query")
        print("DEBUG: Classification state:")
        try:
            if not state.get("query"):
                state["error"] = "No query provided for classification"
                return state

            classification = self.classifier.classify_text(state["query"])

            if classification not in ["S", "M", "A"]:
                state["error"] = f"Invalid classification: {classification}"
                return state

            logger.debug(f"Query classified as: {classification}")
            print(f"[DEBUG] Query classified as: {classification}")
            return {**state, "classification": classification, "error": None}

        except Exception as e:
            state["error"] = f"Error in classify_query: {str(e)}"
            logger.error(state["error"])
            return state

    def select_model(self, state: dict) -> dict:
        """Select a model from the tier based on classification and retry count."""
        logger.debug("Selecting model")
        print("DEBUG: Model selection state:")
        state = dict(state)

        try:
            tier = state.get("classification")
            if not tier:
                state["error"] = "No classification available"
                return state

            tier_key = self._map_classification_to_tier(tier)
            print(f"[DEBUG] Mapped classification {tier} to tier key {tier_key}")
            models = self.models_config.get(tier_key, [])

            if not models:
                state["error"] = f"No models available for {tier_key}"
                return state

            retry_count = state.get("retry_count", 0)
            max_retries = len(models) * MAX_RETRIES_PER_MODEL

            if retry_count >= max_retries:
                state["error"] = f"Max retries ({max_retries}) exceeded for {tier_key}"
                return state

            model_idx = retry_count % len(models)
            selected_model = models[model_idx]

            if isinstance(selected_model, (list, tuple)) and len(selected_model) > 1:
                selected_model = selected_model[1]

            state.update({
                "model_tier": tier_key,
                "selected_model": selected_model,
                "retry_count": retry_count + 1,
                "error": None,
            })

            logger.info(f"Selected model: {selected_model} for tier {tier_key} (attempt {retry_count + 1}/{max_retries})")
            print(f"[INFO] Selected model: {selected_model} for tier {tier_key} (attempt {retry_count + 1}/{max_retries})")
            return state

        except Exception as e:
            state["error"] = f"Error in select_model: {str(e)}"
            logger.error(state["error"])
            return state

    def call_llm(self, state: dict) -> dict:
        """Call the LLM client with the selected model."""
        logger.debug("Calling LLM")
        print("DEBUG: LLM call state:")
        if not state.get("selected_model"):
            return {**state, "error": "No model selected for LLM call"}

        try:
            model_identifier = state["selected_model"]
            print(f"[DEBUG] Using model identifier: {model_identifier}")
            if isinstance(model_identifier, (list, tuple)) and len(model_identifier) > 1:
                model_identifier = model_identifier[1]

            if self.llm_client:
                result = self.llm_client.call(
                    model_identifier,
                    [{"role": "user", "content": state["query"]}],
                    state["model_tier"],
                )
                
                if isinstance(result, dict):
                    actual_model = result.get("model", state["selected_model"])
                    logger.info(f"✅ LLM Response received from {actual_model}")
                    return {
                        **state, 
                        "llm_response": result,
                        "used_model": actual_model
                    }
                else:
                    return {
                        **state, 
                        "llm_response": result, 
                        "used_model": state["selected_model"]
                    }
            else:
                logger.warning("No LLM client provided, using mock response")
                response = f"Response for: {state['query']} from {model_identifier}"
                return {**state, "llm_response": response, "used_model": state["selected_model"]}

        except Exception as e:
            logger.error(f"❌ LLM call failed: {str(e)}")
            return {**state, "error": str(e)}

    def store_in_cache(self, state: dict) -> dict:
        """Store the LLM response in the semantic cache if not already cached."""
        try:
            if state.get("llm_response") and not state.get("cache_hit", False):
                query = state["query"]
                response = state["llm_response"]
                if isinstance(response, dict) and "response" in response:
                    response_text = response["response"]
                else:
                    response_text = str(response)

                self.cache.set(query, response_text)
                logger.debug(f"Stored response in semantic cache for query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to store in cache: {str(e)}")
        return state

    def route(self, query: str, user_models: dict = None) -> Dict[str, Any]:
        """Run a query through the routing logic - same as langgraph_router."""
        
        # Initialize state
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
        state = self.check_cache(state)
        if state.get("cache_hit"):
            return state

        # Step 2: Classify query
        state = self.classify_query(state)
        if state.get("error"):
            return state

        # Step 3: Select model and call LLM with retries
        tier_key = self._map_classification_to_tier(state["classification"])
        models = self.models_config.get(tier_key, [])
        max_attempts = len(models) * self.max_retries if models else 0

        while state.get("retry_count", 0) < max_attempts:
            # Select model
            state = self.select_model(state)
            if state.get("error") and "Max retries" in state.get("error", ""):
                break

            # Call LLM
            state = self.call_llm(state)
            
            # Check if successful
            if state.get("llm_response") and not state.get("error"):
                # Store in cache and return
                state = self.store_in_cache(state)
                return state
            
            # If error, continue to retry
            logger.warning(f"Model {state.get('selected_model')} failed, retrying...")

        return state
