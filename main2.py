"""
Dynamic LLM Routing System - Main Package
==========================================

A complete package that integrates all components of the LLM routing system.
Easy to use, integrate with frontend, and extend.

Author: Your Name
Version: 1.0.0
"""

import os
import time
import uuid
from typing import Dict, List, Optional, Literal, Any
from dataclasses import dataclass, asdict
import json

# Import all project components
from semantic_cache import SemanticCache
from langgraph_router import Router
from classifier import classify_text
from config import Classifier, LLMClient, MODELS_CONFIG
from logger_config import setup_logger

# Import new professional features
from monitoring import AdvancedMonitoring
from rate_limiter import RateLimiter, RateLimitConfig, DDoSProtection
from quality_evaluator import QualityEvaluator
from ab_testing import ABTestingFramework


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class QueryRequest:
    """Request model for query processing"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QueryResponse:
    """Response model for query processing"""
    success: bool
    query: str
    response: str
    classification: str  # S, M, or A
    model_tier: str  # tier1, tier2, or tier3
    used_model: str
    cache_hit: bool
    processing_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    quality_score: Optional[Dict[str, Any]] = None  # New: quality evaluation
    rate_limit_info: Optional[Dict[str, Any]] = None  # New: rate limit info
    ab_test_variant: Optional[str] = None  # New: A/B test variant
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class SystemStats:
    """System statistics"""
    total_queries: int
    cache_hits: int
    cache_hit_rate: float
    avg_processing_time: float
    queries_by_tier: Dict[str, int]
    queries_by_classification: Dict[str, int]


# ============================================================================
# Main LLM Router System Class
# ============================================================================

class DynamicLLMRouter:
    """
    Main class for Dynamic LLM Routing System
    
    This class integrates all components:
    - Semantic caching for faster responses
    - Query classification (Simple/Medium/Advanced)
    - Dynamic model selection based on complexity
    - Fallback mechanisms for reliability
    - Logging and statistics
    
    Example Usage:
    -------------
    ```python
    # Initialize the router
    router_system = DynamicLLMRouter()
    
    # Process a single query
    response = router_system.process_query("What is the capital of France?")
    print(response.response)
    
    # Get system statistics
    stats = router_system.get_stats()
    print(f"Cache hit rate: {stats.cache_hit_rate:.2%}")
    ```
    """
    
    def __init__(
        self,
        cache_ttl: int = 3600,
        cache_threshold: float = 0.5,
        max_retries: int = 3,
        enable_logging: bool = True,
        log_level: str = "INFO",
        enable_monitoring: bool = True,
        enable_rate_limiting: bool = True,
        enable_quality_eval: bool = True,
        enable_ab_testing: bool = False,
        user_tier: str = "free",
        db_session = None
    ):
        """
        Initialize the Dynamic LLM Router System
        
        Args:
            cache_ttl: Time to live for cache entries in seconds (default: 3600)
            cache_threshold: Similarity threshold for semantic cache (default: 0.5)
            max_retries: Maximum retry attempts for failed requests (default: 3)
            enable_logging: Enable logging (default: True)
            log_level: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)
            enable_monitoring: Enable advanced monitoring (default: True)
            enable_rate_limiting: Enable rate limiting (default: True)
            enable_quality_eval: Enable quality evaluation (default: True)
            enable_ab_testing: Enable A/B testing (default: False)
            user_tier: User tier for rate limiting (default: "free")
        """
        # Setup logger
        self.logger = setup_logger("llm_router", level=log_level) if enable_logging else None
        if self.logger:
            self.logger.info("🚀 Initializing Dynamic LLM Router System with Professional Features...")
        
        # Store configuration
        self.user_tier = user_tier
        self.enable_monitoring = enable_monitoring
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_quality_eval = enable_quality_eval
        self.enable_ab_testing = enable_ab_testing
        
        # Initialize components
        try:
            self.cache = SemanticCache(
                cache_file="semantic_cache.json",
                threshold=cache_threshold,
                default_ttl=cache_ttl
            )
            if self.logger:
                self.logger.info("✅ Semantic cache initialized")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Cache initialization failed: {e}")
            self.cache = None
        
        # Initialize classifier
        self.classifier = Classifier()
        if self.logger:
            self.logger.info("✅ Classifier initialized")
        
        # Initialize LLM client
        self.llm_client = LLMClient(MODELS_CONFIG)
        if self.logger:
            self.logger.info("✅ LLM client initialized")
        
        # Store db_session for model ratings
        self.db_session = db_session
        
        # Initialize router with LangGraph
        self.router = Router(
            models_config={
                "tier1": [m[1] for m in MODELS_CONFIG["tier1"]],
                "tier2": [m[1] for m in MODELS_CONFIG["tier2"]],
                "tier3": [m[1] for m in MODELS_CONFIG["tier3"]],
            },
            cache=self.cache,
            classifier=self.classifier,
            llm_client=self.llm_client,
            max_retries=max_retries,
            db_session=db_session
        )
        if self.logger:
            self.logger.info("✅ LangGraph router initialized")
        
        # Statistics tracking
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "processing_times": [],
            "queries_by_tier": {"tier1": 0, "tier2": 0, "tier3": 0},
            "queries_by_classification": {"S": 0, "M": 0, "A": 0}
        }
        
        # Initialize monitoring system
        self.monitoring = None
        if enable_monitoring:
            try:
                self.monitoring = AdvancedMonitoring(
                    metrics_file="metrics/query_metrics.jsonl",
                    window_size=1000,
                    enable_alerts=True
                )
                if self.logger:
                    self.logger.info("✅ Monitoring system initialized")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ Monitoring initialization failed: {e}")
        
        # Initialize rate limiter
        self.rate_limiter = None
        self.ddos_protection = None
        if enable_rate_limiting:
            try:
                self.rate_limiter = RateLimiter(config=RateLimitConfig())
                self.ddos_protection = DDoSProtection()
                if self.logger:
                    self.logger.info("✅ Rate limiting initialized")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ Rate limiting initialization failed: {e}")
        
        # Initialize quality evaluator
        self.quality_evaluator = None
        if enable_quality_eval:
            try:
                self.quality_evaluator = QualityEvaluator(
                    min_acceptable_score=60.0,
                    enable_safety_check=True
                )
                if self.logger:
                    self.logger.info("✅ Quality evaluator initialized")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ Quality evaluator initialization failed: {e}")
        
        # Initialize A/B testing framework
        self.ab_testing = None
        if enable_ab_testing:
            try:
                self.ab_testing = ABTestingFramework()
                if self.logger:
                    self.logger.info("✅ A/B testing framework initialized")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ A/B testing initialization failed: {e}")
        
        if self.logger:
            self.logger.info("✅ System initialization complete with all professional features!")
    
    
    def process_query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        ab_test_id: Optional[str] = None,
        user_models: Optional[Dict[str, List]] = None
    ) -> QueryResponse:
        """
        Process a single query through the routing system with professional features
        
        Args:
            query: The user's query text
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Optional additional metadata
            ip_address: Optional IP address for rate limiting
            ab_test_id: Optional A/B test ID
        
        Returns:
            QueryResponse object containing the result and metadata
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())
        
        # تحديث ترتيب الموديلات قبل كل query
        if self.db_session:
            try:
                self.router.refresh_model_rankings()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to refresh model rankings: {e}")
        
        if self.logger:
            self.logger.info(f"📥 Processing query [{query_id}]: {query[:50]}...")
        
        # Check DDoS protection
        if self.ddos_protection and ip_address:
            allowed, ddos_reason = self.ddos_protection.check_request(ip_address)
            if not allowed:
                if self.logger:
                    self.logger.warning(f"🚨 DDoS Protection: {ddos_reason}")
                return self._create_error_response(
                    query, ddos_reason, start_time, user_id, session_id
                )
        
        # Check rate limits
        rate_limit_info = None
        if self.rate_limiter:
            identifier = ip_address or user_id or session_id or "anonymous"
            allowed, limit_reason = self.rate_limiter.check_rate_limit(
                identifier, user_id, self.user_tier
            )
            
            if not allowed:
                if self.logger:
                    self.logger.warning(f"⚠️ Rate limit exceeded: {limit_reason}")
                
                rate_limit_info = self.rate_limiter.get_rate_limit_headers(identifier, self.user_tier)
                
                return self._create_error_response(
                    query, f"Rate limit exceeded: {limit_reason}", 
                    start_time, user_id, session_id, rate_limit_info
                )
            
            rate_limit_info = self.rate_limiter.get_rate_limit_headers(identifier, self.user_tier)
        
        try:
            # Handle A/B testing if enabled
            ab_variant = None
            if self.ab_testing and ab_test_id:
                variant_info = self.ab_testing.get_variant_for_request(ab_test_id, user_id)
                if variant_info:
                    ab_variant = variant_info[0]
                    # In production, you would override model selection here
            
            # Route the query through LangGraph (with user models if provided)
            result = self.router.route(query, user_models=user_models)
            
            # Extract response
            if isinstance(result.get("llm_response"), dict):
                response_text = result["llm_response"].get("response", str(result["llm_response"]))
            else:
                response_text = str(result.get("llm_response") or result.get("cached_response", ""))
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            if self.logger:
                self.logger.info(f"[DEBUG] Step 1: Got LLM response, time={processing_time:.2f}s")
            
            # Evaluate quality if enabled
            quality_score_data = None
            if self.quality_evaluator and response_text:
                if self.logger:
                    self.logger.info(f"[DEBUG] Step 2: Starting quality evaluation...")
                try:
                    quality_score = self.quality_evaluator.evaluate(
                        query=query,
                        response=response_text,
                        classification=result.get("classification"),
                        model=result.get("used_model")
                    )
                    quality_score_data = asdict(quality_score)
                    
                    if self.logger:
                        self.logger.info(f"[DEBUG] Step 2: Quality evaluation done")
                    
                    if self.logger and quality_score.recommendation == "reject":
                        self.logger.warning(
                            f"⚠️ Low quality response detected: {quality_score.overall_score:.1f}/100"
                        )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Quality evaluation failed: {e}")
            
            if self.logger:
                self.logger.info(f"[DEBUG] Step 3: Updating statistics...")
            
            # Update statistics
            self._update_stats(result, processing_time)
            
            if self.logger:
                self.logger.info(f"[DEBUG] Step 4: Recording monitoring data...")
            
            # Record monitoring data
            if self.monitoring:
                try:
                    self.monitoring.record_query(
                        query_id=query_id,
                        query_text=query,
                        classification=result.get("classification", "Unknown"),
                        tier=result.get("model_tier", "tier1"),
                        model_used=result.get("used_model", "Unknown"),
                        cache_hit=result.get("cache_hit", False),
                        processing_time=processing_time,
                        success=True,
                        tokens_used=result.get("llm_response", {}).get("input_tokens") if isinstance(result.get("llm_response"), dict) else None,
                        cost=result.get("llm_response", {}).get("cost") if isinstance(result.get("llm_response"), dict) else None,
                        response_length=len(response_text),
                        user_id=user_id,
                        session_id=session_id
                    )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Monitoring recording failed: {e}")
            
            if self.logger:
                self.logger.info(f"[DEBUG] Step 5: Creating response object...")
            
            # Record A/B test result
            if self.ab_testing and ab_test_id and ab_variant:
                try:
                    self.ab_testing.record_result(
                        test_id=ab_test_id,
                        variant_name=ab_variant,
                        success=True,
                        response_time=processing_time,
                        cost=result.get("llm_response", {}).get("cost", 0.0) if isinstance(result.get("llm_response"), dict) else 0.0,
                        quality_score=quality_score_data.get("overall_score") if quality_score_data else None
                    )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"A/B testing recording failed: {e}")
            
            # Create response object
            response = QueryResponse(
                success=True,
                query=query,
                response=response_text,
                classification=result.get("classification", "Unknown"),
                model_tier=result.get("model_tier", "tier1"),
                used_model=result.get("used_model", "Unknown"),
                cache_hit=result.get("cache_hit", False),
                processing_time=processing_time,
                error=result.get("error"),
                metadata={
                    "query_id": query_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "custom_metadata": metadata,
                    "retry_count": result.get("retry_count", 0),
                    "ip_address": ip_address
                },
                quality_score=quality_score_data,
                rate_limit_info=rate_limit_info,
                ab_test_variant=ab_variant
            )
            
            if self.logger:
                self.logger.info(
                    f"✅ Query processed | "
                    f"Time: {processing_time:.2f}s | "
                    f"Cache: {'HIT' if response.cache_hit else 'MISS'} | "
                    f"Tier: {response.model_tier}"
                )
                self.logger.info(f"[DEBUG] Step 6: Returning response to API...")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            if self.logger:
                self.logger.error(f"❌ Query processing failed: {str(e)}")
            
            # Record failure in monitoring
            if self.monitoring:
                try:
                    self.monitoring.record_query(
                        query_id=query_id,
                        query_text=query,
                        classification="Error",
                        tier="unknown",
                        model_used="error",
                        cache_hit=False,
                        processing_time=processing_time,
                        success=False,
                        error=str(e),
                        response_length=0,
                        user_id=user_id,
                        session_id=session_id
                    )
                except:
                    pass
            
            return self._create_error_response(
                query, str(e), start_time, user_id, session_id, rate_limit_info
            )
    
    
    def process_batch(
        self,
        queries: List[str],
        show_progress: bool = True
    ) -> List[QueryResponse]:
        """
        Process multiple queries in batch
        
        Args:
            queries: List of query strings
            show_progress: Show progress output (default: True)
        
        Returns:
            List of QueryResponse objects
        """
        if self.logger:
            self.logger.info(f"📦 Processing batch of {len(queries)} queries...")
        
        results = []
        for i, query in enumerate(queries, 1):
            if show_progress:
                print(f"Processing {i}/{len(queries)}: {query[:50]}...")
            
            response = self.process_query(query)
            results.append(response)
        
        if self.logger:
            self.logger.info(f"✅ Batch processing complete: {len(results)} queries processed")
        
        return results
    
    
    def classify_query_only(self, query: str) -> Literal["S", "M", "A"]:
        """
        Classify a query without processing it (useful for preview)
        
        Args:
            query: The query text to classify
        
        Returns:
            Classification: "S" (Simple), "M" (Medium), or "A" (Advanced)
        """
        return classify_text(query)
    
    
    def check_cache(self, query: str) -> Optional[str]:
        """
        Check if a query exists in cache without processing
        
        Args:
            query: The query text to check
        
        Returns:
            Cached response if found, None otherwise
        """
        if self.cache:
            return self.cache.get(query)
        return None
    
    
    def clear_cache(self) -> None:
        """Clear all cached responses"""
        if self.cache:
            self.cache.cache = []
            self.cache._save_cache()
            if self.logger:
                self.logger.info("🗑️ Cache cleared")
    
    
    def get_stats(self) -> SystemStats:
        """
        Get system statistics
        
        Returns:
            SystemStats object with current statistics
        """
        total = self._stats["total_queries"]
        cache_hits = self._stats["cache_hits"]
        
        return SystemStats(
            total_queries=total,
            cache_hits=cache_hits,
            cache_hit_rate=cache_hits / total if total > 0 else 0.0,
            avg_processing_time=sum(self._stats["processing_times"]) / len(self._stats["processing_times"]) if self._stats["processing_times"] else 0.0,
            queries_by_tier=self._stats["queries_by_tier"].copy(),
            queries_by_classification=self._stats["queries_by_classification"].copy()
        )
    
    
    def reset_stats(self) -> None:
        """Reset all statistics"""
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "processing_times": [],
            "queries_by_tier": {"tier1": 0, "tier2": 0, "tier3": 0},
            "queries_by_classification": {"S": 0, "M": 0, "A": 0}
        }
        if self.logger:
            self.logger.info("📊 Statistics reset")
    
    
    def _update_stats(self, result: Dict, processing_time: float) -> None:
        """Internal method to update statistics"""
        self._stats["total_queries"] += 1
        self._stats["processing_times"].append(processing_time)
        
        if result.get("cache_hit"):
            self._stats["cache_hits"] += 1
        
        tier = result.get("model_tier", "tier1")
        if tier in self._stats["queries_by_tier"]:
            self._stats["queries_by_tier"][tier] += 1
        
        classification = result.get("classification", "S")
        if classification in self._stats["queries_by_classification"]:
            self._stats["queries_by_classification"][classification] += 1
    
    
    def _create_error_response(
        self,
        query: str,
        error: str,
        start_time: float,
        user_id: Optional[str],
        session_id: Optional[str],
        rate_limit_info: Optional[Dict] = None
    ) -> QueryResponse:
        """Create error response"""
        processing_time = time.time() - start_time
        return QueryResponse(
            success=False,
            query=query,
            response="",
            classification="Error",
            model_tier="unknown",
            used_model="error",
            cache_hit=False,
            processing_time=processing_time,
            error=error,
            metadata={"user_id": user_id, "session_id": session_id},
            rate_limit_info=rate_limit_info
        )
    
    def get_monitoring_dashboard(self) -> None:
        """Display monitoring dashboard"""
        if self.monitoring:
            self.monitoring.print_dashboard()
        else:
            print("⚠️ Monitoring is not enabled")
    
    def get_rate_limit_stats(self) -> Dict:
        """Get rate limiting statistics"""
        if self.rate_limiter:
            return self.rate_limiter.get_stats()
        return {"error": "Rate limiting not enabled"}
    
    def export_monitoring_data(self, output_file: str):
        """Export monitoring data to file"""
        if self.monitoring:
            self.monitoring.export_metrics(output_file)
        else:
            print("⚠️ Monitoring is not enabled")
    
    def print_stats(self) -> None:
        """Print formatted statistics to console"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 SYSTEM STATISTICS")
        print("="*60)
        print(f"Total Queries Processed: {stats.total_queries}")
        print(f"Cache Hits: {stats.cache_hits} ({stats.cache_hit_rate:.1%})")
        print(f"Average Processing Time: {stats.avg_processing_time:.2f}s")
        print("\nQueries by Tier:")
        for tier, count in stats.queries_by_tier.items():
            print(f"  {tier}: {count}")
        print("\nQueries by Classification:")
        for classification, count in stats.queries_by_classification.items():
            print(f"  {classification}: {count}")
        print("="*60 + "\n")
        
        # Print advanced monitoring if available
        if self.enable_monitoring:
            print("\n📈 For detailed monitoring, use: router.get_monitoring_dashboard()")


# ============================================================================
# Convenience Functions
# ============================================================================

def quick_query(query: str) -> str:
    """
    Quick function to process a single query without initialization overhead
    (Creates a router instance, processes query, returns response text)
    
    Args:
        query: The query text
    
    Returns:
        Response text string
    """
    router = DynamicLLMRouter(enable_logging=False)
    response = router.process_query(query)
    return response.response


def get_model_info() -> Dict[str, List[str]]:
    """
    Get information about available models in each tier
    
    Returns:
        Dictionary with tier names and model lists
    """
    return {
        "tier1": [m[0] for m in MODELS_CONFIG["tier1"]],
        "tier2": [m[0] for m in MODELS_CONFIG["tier2"]],
        "tier3": [m[0] for m in MODELS_CONFIG["tier3"]],
    }


# ============================================================================
# Example Usage & Testing
# ============================================================================

def example_usage():
    """Example usage demonstration"""
    print("\n" + "="*60)
    print("🚀 Dynamic LLM Router - Example Usage")
    print("="*60 + "\n")
    
    # Initialize the system
    print("1️⃣ Initializing router system...")
    router = DynamicLLMRouter(
        cache_ttl=600,
        enable_logging=True,
        log_level="INFO"
    )
    
    # Single query example
    print("\n2️⃣ Processing single query...")
    response = router.process_query("What is the capital of Egypt?")
    print(f"\n📝 Query: {response.query}")
    print(f"💬 Response: {response.response}")
    print(f"🎯 Classification: {response.classification}")
    print(f"⚡ Time: {response.processing_time:.2f}s")
    print(f"💾 Cache Hit: {response.cache_hit}")
    
    # Batch processing example
    print("\n3️⃣ Processing batch queries...")
    test_queries = [
        "What is 2 + 2?",
        "Explain quantum computing briefly.",
        "Create a Python function to sort a list."
    ]
    responses = router.process_batch(test_queries, show_progress=True)
    
    # Classification preview
    print("\n4️⃣ Classification preview (without processing)...")
    test_query = "Design a complex microservices architecture"
    classification = router.classify_query_only(test_query)
    print(f"Query: {test_query}")
    print(f"Classification: {classification}")
    
    # System statistics
    print("\n5️⃣ System statistics...")
    router.print_stats()
    
    # Export response as JSON
    print("\n6️⃣ Export response as JSON...")
    json_output = response.to_json()
    print("JSON Output:")
    print(json_output)
    
    print("\n✅ Example complete!\n")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run example usage
    example_usage()
    
    # Uncomment below for interactive mode
    # router = DynamicLLMRouter()
    # while True:
    #     query = input("\n🔍 Enter your query (or 'quit' to exit): ")
    #     if query.lower() in ['quit', 'exit', 'q']:
    #         break
    #     response = router.process_query(query)
    #     print(f"\n💬 Response: {response.response}\n")
