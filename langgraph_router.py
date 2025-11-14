import logging
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END

MAX_RETRIES_PER_MODEL = 3
WORKFLOW_RECURSION_LIMIT = 50  # Increased to handle retries across multiple models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RouterState(TypedDict):
    """The state of the router workflow."""


    query: str


    classification: Optional[Literal["S", "M", "A"]]


    model_tier: Optional[Literal["tier1", "tier2", "tier3"]]
    selected_model: Optional[str]


    cache_hit: bool
    cached_response: Optional[str]


    llm_response: Optional[str]
    used_model: Optional[str]


    error: Optional[str]
    retry_count: int


class Router:
    """
    LangGraph-based router for handling query classification,
    model selection, caching, and retries.
    """

    def __init__(
        self,
        models_config: dict,
        cache,
        classifier,
        llm_client=None,
        db_session=None,  # Add database session for ratings
        max_retries: int = MAX_RETRIES_PER_MODEL,
    ):
        self.models_config = models_config
        self.cache = cache
        self.classifier = classifier
        self.llm_client = llm_client
        self.max_retries = max_retries
        self.db_session = db_session
        self.workflow = self._create_workflow()
        
        # Load dynamic model ranking
        self._load_ranked_models()


    def store_in_cache(self, state: RouterState) -> RouterState:
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
            return state
        except Exception as e:
            logger.warning(f"Failed to store in cache: {str(e)}")
            return state

    def check_cache(self, state: RouterState) -> RouterState:
        """Check if the query already exists in the semantic cache."""
        logger.debug("Checking cache for query")
        print("DEBUG: Cache check state:")
        response = self.cache.get(state["query"])
        if response is not None:
            return {
                **state,
                "cache_hit": True,
                "cached_response": response,
                "llm_response": response,
            }
        return {**state, "cache_hit": False}


    def classify_query(self, state: RouterState) -> RouterState:
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


    def select_model(self, state: RouterState) -> RouterState:
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

            state.update(
                {
                    "model_tier": tier_key,
                    "selected_model": selected_model,
                    "retry_count": retry_count + 1,
                    "error": None,
                }
            )

            logger.info(
                f"Selected model: {selected_model} for tier {tier_key} (attempt {retry_count + 1}/{max_retries})"
            )
            print(f"[INFO] Selected model: {selected_model} for tier {tier_key} (attempt {retry_count + 1}/{max_retries})")
            return state

        except Exception as e:
            state["error"] = f"Error in select_model: {str(e)}"
            logger.error(state["error"])
            return state

    def _map_classification_to_tier(self, classification: str) -> str:
        """Helper to map classification letter to tier key."""
        mapping = {"S": "tier1", "M": "tier2", "A": "tier3"}
        return mapping.get(classification, "tier1")


    def call_llm(self, state: RouterState) -> RouterState:
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
                
                # Handle response format - fallback returns dict with metadata
                if isinstance(result, dict):
                    response_text = result.get("response", str(result))
                    actual_model = result.get("model", state["selected_model"])
                    logger.info(f"✅ LLM Response received from {actual_model}")
                    return {
                        **state, 
                        "llm_response": result,  # Store full result for metadata
                        "used_model": actual_model
                    }
                else:
                    response_text = str(result)
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


    def handle_error(self, state: RouterState) -> RouterState:
        """Pass through state after error."""
        return state

    def should_use_cache(self, state: RouterState) -> str:
        """Decide whether to use cache or classify query."""
        return "use_cache" if state.get("cache_hit") else "classify"

    def handle_llm_response(self, state: RouterState) -> str:
        """Decide next step after LLM response."""
        print("DEBUG: LLM response handler state:")
        
        # Success condition - we have a valid response
        if state.get("llm_response"):
            return "success"

        # Check retry limits
        retry_count = state.get("retry_count", 0)
        tier = state.get("classification", "S")
        max_models = len(self.models_config.get(self._map_classification_to_tier(tier), []))
        max_retries = max_models * MAX_RETRIES_PER_MODEL

        # If we've exceeded max retries, it's an error
        if retry_count >= max_retries:
            if not state.get("error"):
                state["error"] = f"Max retries ({max_retries}) exceeded"
            return "error"

        # If there's an explicit error, retry
        if state.get("error"):
            return "retry"

        # Default: if no response and no error (shouldn't happen), treat as error
        state["error"] = "No response generated - unexpected state"
        return "error"

    def should_retry(self, state: RouterState) -> str:
        """Decide whether to retry or fail after error."""
        retry_count = state.get("retry_count", 0)
        tier = state.get("classification", "S")
        max_models = len(self.models_config.get(self._map_classification_to_tier(tier), []))
        max_retries = max_models * MAX_RETRIES_PER_MODEL

        return "retry" if retry_count < max_retries else "fail"


    def _create_workflow(self):
        """Build LangGraph workflow with nodes and edges."""
        builder = StateGraph(RouterState)

        # Define nodes
        builder.add_node("check_cache", self.check_cache)
        builder.add_node("classify_query", self.classify_query)
        builder.add_node("select_model", self.select_model)
        builder.add_node("call_llm", self.call_llm)
        builder.add_node("handle_error", self.handle_error)
        builder.add_node("store_in_cache", self.store_in_cache)

        # Define edges
        builder.set_entry_point("check_cache")
        builder.add_conditional_edges("check_cache", self.should_use_cache, {"use_cache": END, "classify": "classify_query"})
        builder.add_edge("classify_query", "select_model")
        builder.add_edge("select_model", "call_llm")
        builder.add_conditional_edges("call_llm", self.handle_llm_response, {"success": "store_in_cache", "retry": "select_model", "error": "handle_error"})
        builder.add_edge("store_in_cache", END)
        builder.add_conditional_edges("handle_error", self.should_retry, {"retry": "select_model", "fail": END})

        # Compile workflow with recursion limit
        workflow = builder.compile()
        
        return workflow


    def route(self, query: str, user_models: dict = None) -> RouterState:
        """Run a query through the workflow and return the final state."""
        
        # Temporarily merge user models with system models
        original_models_config = self.models_config.copy()
        if user_models:
            # Prepend user models to each tier
            for tier in ['tier1', 'tier2', 'tier3']:
                if tier in user_models and user_models[tier]:
                    # Add user models at the beginning of the tier
                    # model_name now contains the full path (e.g., qwen/qwen-2.5-72b-instruct:free)
                    user_model_ids = [m['env_var_name'] for m in user_models[tier]]
                    self.models_config[tier] = user_model_ids + self.models_config[tier]
            
            # Update LLMClient with user models and their API keys
            self._update_llm_client_with_user_models(user_models)
        
        initial_state = RouterState(
            query=query,
            classification=None,
            model_tier=None,
            selected_model=None,
            cache_hit=False,
            cached_response=None,
            llm_response=None,
            used_model=None,
            error=None,
            retry_count=0,
        )
        # Pass recursion limit config to the workflow
        config = {"recursion_limit": WORKFLOW_RECURSION_LIMIT}
        result = self.workflow.invoke(initial_state, config=config)
        
        # Restore original models_config
        if user_models:
            self.models_config = original_models_config
        
        return result
    
    def _update_llm_client_with_user_models(self, user_models: dict):
        """Update LLMClient with user models and their API keys"""
        try:
            # Convert models_config to the format expected by LLMClient
            from config import MODELS_CONFIG
            updated_config = {}
            
            for tier, model_ids in self.models_config.items():
                tier_models = []
                for model_id in model_ids:
                    # model_id should already be the full path from the database
                    # e.g., deepseek/deepseek-chat-v3.1:free
                    
                    # Search for the model in the original config
                    found = False
                    for original_model in MODELS_CONFIG.get(tier, []):
                        if isinstance(original_model, (list, tuple)) and len(original_model) >= 2:
                            if original_model[1] == model_id:
                                tier_models.append(original_model)
                                found = True
                                break
                        elif original_model == model_id:
                            tier_models.append([model_id.split('/')[-1].replace(':free', ''), model_id])
                            found = True
                            break
                    
                    # If not found in original config, it's a user-added model
                    if not found:
                        # Use the full model_id as the identifier
                        model_name = model_id.split('/')[-1].replace(':free', '') if '/' in model_id else model_id
                        tier_models.append([model_name, model_id])
                
                if not tier_models:
                    tier_models = MODELS_CONFIG.get(tier, [])
                
                updated_config[tier] = tier_models
            
            # Extract user API keys
            user_api_keys = {}
            for tier, models_list in user_models.items():
                for model in models_list:
                    if 'model_path' in model and 'api_key' in model:
                        user_api_keys[model['model_path']] = model['api_key']
            
            # Update LLMClient
            if hasattr(self.llm_client, 'update_models_config'):
                self.llm_client.update_models_config(updated_config, user_api_keys)
                logger.info("✅ Updated LLMClient with user models")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not update LLMClient with user models: {e}")
    
    def _load_ranked_models(self):
        """Load models ranked by points from database"""
        if not self.db_session:
            return
        
        try:
            from model_rating_system import ModelRatingManager
            rating_manager = ModelRatingManager(self.db_session)
            
            # Get ranked models for each tier
            ranked_models = rating_manager.get_all_ranked_models()
            
            # Update models_config with new ranking
            for tier, model_list in ranked_models.items():
                if tier in self.models_config and model_list:
                    # Replace old list with ranked list
                    self.models_config[tier] = model_list
                    logger.info(f"✅ Loaded {len(model_list)} ranked models for {tier}")
            
            # Update LLMClient with new ranking
            if hasattr(self.llm_client, 'update_models_config'):
                # Convert model identifiers to format required by LLMClient
                # LLMClient needs list of tuples [name, identifier]
                from config import MODELS_CONFIG
                updated_config = {}
                for tier, ranked_ids in ranked_models.items():
                    # Search for models in original MODELS_CONFIG and order them
                    tier_models = []
                    for model_id in ranked_ids:
                        # Search for model in original config
                        found = False
                        for original_model in MODELS_CONFIG.get(tier, []):
                            if isinstance(original_model, (list, tuple)) and len(original_model) >= 2:
                                if original_model[1] == model_id:
                                    tier_models.append(original_model)
                                    found = True
                                    break
                            elif original_model == model_id:
                                tier_models.append([model_id.split('/')[-1].replace(':free', ''), model_id])
                                found = True
                                break
                        
                        # If not found in original config, it might be a user-added model
                        if not found:
                            # 为用户添加的模型创建 tuple
                            model_name = model_id.split('/')[-1].replace(':free', '')
                            tier_models.append([model_name, model_id])
                    
                    # If no ranked models found, use originals
                    if not tier_models:
                        tier_models = MODELS_CONFIG.get(tier, [])
                    
                    updated_config[tier] = tier_models
                
                # Extract user API keys from user_models
                user_api_keys = {}
                if user_models:
                    for tier, models_list in user_models.items():
                        for model in models_list:
                            if 'model_path' in model and 'api_key' in model:
                                user_api_keys[model['model_path']] = model['api_key']
                
                self.llm_client.update_models_config(updated_config, user_api_keys)
                logger.info("✅ Updated LLMClient with ranked models")
        
        except Exception as e:
            logger.warning(f"⚠️  Could not load ranked models: {e}, using default order")
    
    def refresh_model_rankings(self):
        """Update model ranking (can be called periodically)"""
        self._load_ranked_models()
