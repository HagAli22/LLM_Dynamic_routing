"""
Production-Ready API Server for Dynamic LLM Router
==================================================
FastAPI-based REST API with all professional features.

Features:
- RESTful API endpoints
- Authentication & authorization
- Rate limiting
- Monitoring integration
- Quality evaluation
- A/B testing support
- Swagger documentation
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uvicorn
from datetime import datetime
import secrets

from main2 import DynamicLLMRouter, QueryResponse
from ab_testing import Variant

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic LLM Router API",
    description="Enterprise-grade LLM routing system with professional features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize router (singleton)
router_instance = None

def get_router() -> DynamicLLMRouter:
    """Get or create router instance"""
    global router_instance
    if router_instance is None:
        router_instance = DynamicLLMRouter(
            cache_ttl=3600,
            enable_logging=True,
            enable_monitoring=True,
            enable_rate_limiting=True,
            enable_quality_eval=True,
            enable_ab_testing=True,
            user_tier="premium"
        )
    return router_instance


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for query processing"""
    query: str = Field(..., description="User query text", min_length=1, max_length=5000)
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    ab_test_id: Optional[str] = Field(None, description="A/B test ID")

class QueryResponseModel(BaseModel):
    """Response model for query processing"""
    success: bool
    query: str
    response: str
    classification: str
    model_tier: str
    used_model: str
    cache_hit: bool
    processing_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    quality_score: Optional[Dict[str, Any]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    ab_test_variant: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    features: Dict[str, bool]

class StatsResponse(BaseModel):
    """System statistics response"""
    total_queries: int
    cache_hits: int
    cache_hit_rate: float
    avg_processing_time: float
    queries_by_tier: Dict[str, int]
    queries_by_classification: Dict[str, int]

class ABTestRequest(BaseModel):
    """A/B test creation request"""
    test_name: str
    variants: List[Dict[str, Any]]
    duration: Optional[int] = 3600
    min_samples: int = 100


# ============================================================================
# Authentication (Simple token-based)
# ============================================================================

# In production, use proper authentication (OAuth2, JWT, etc.)
API_KEYS = {
    "demo_key": "free",
    "premium_key": "premium",
    "enterprise_key": "enterprise"
}

def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Verify API key and return user tier"""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="API key required")
    
    tier = API_KEYS.get(x_api_key)
    if tier is None:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return tier


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Dynamic LLM Router API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    router = get_router()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0",
        features={
            "monitoring": router.enable_monitoring,
            "rate_limiting": router.enable_rate_limiting,
            "quality_eval": router.enable_quality_eval,
            "ab_testing": router.enable_ab_testing
        }
    )


@app.post("/query", response_model=QueryResponseModel)
async def process_query(
    request: QueryRequest,
    request_obj: Request,
    tier: str = Depends(verify_api_key)
):
    """
    Process a query through the LLM router
    
    - **query**: The user's query text
    - **user_id**: Optional user identifier
    - **session_id**: Optional session identifier
    - **metadata**: Optional additional metadata
    - **ab_test_id**: Optional A/B test ID
    """
    router = get_router()
    
    # Get client IP
    client_ip = request_obj.client.host
    
    try:
        # Update router tier based on API key
        router.user_tier = tier
        
        # Process query
        response = router.process_query(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata,
            ip_address=client_ip,
            ab_test_id=request.ab_test_id
        )
        
        return QueryResponseModel(**response.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch", response_model=List[QueryResponseModel])
async def process_batch(
    queries: List[str],
    request_obj: Request,
    tier: str = Depends(verify_api_key)
):
    """Process multiple queries in batch"""
    router = get_router()
    router.user_tier = tier
    
    client_ip = request_obj.client.host
    
    try:
        responses = []
        for query in queries:
            response = router.process_query(
                query=query,
                ip_address=client_ip
            )
            responses.append(QueryResponseModel(**response.to_dict()))
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats(tier: str = Depends(verify_api_key)):
    """Get system statistics"""
    router = get_router()
    stats = router.get_stats()
    
    return StatsResponse(**stats.__dict__)


@app.get("/monitoring/dashboard")
async def get_monitoring_dashboard(tier: str = Depends(verify_api_key)):
    """Get monitoring dashboard data"""
    router = get_router()
    
    if not router.monitoring:
        raise HTTPException(status_code=503, detail="Monitoring not enabled")
    
    metrics = router.monitoring.get_aggregated_metrics(time_window=3600)
    model_perf = router.monitoring.get_model_performance()
    cost_analysis = router.monitoring.get_cost_analysis(time_window=3600)
    
    return {
        "metrics": metrics.__dict__,
        "model_performance": [m.__dict__ for m in model_perf],
        "cost_analysis": cost_analysis
    }


@app.get("/monitoring/export")
async def export_monitoring(tier: str = Depends(verify_api_key)):
    """Export monitoring data"""
    router = get_router()
    
    if not router.monitoring:
        raise HTTPException(status_code=503, detail="Monitoring not enabled")
    
    # Generate unique filename
    filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    router.export_monitoring_data(filename)
    
    return {"message": "Metrics exported", "filename": filename}


@app.get("/rate-limit/stats")
async def get_rate_limit_stats(tier: str = Depends(verify_api_key)):
    """Get rate limiting statistics"""
    router = get_router()
    return router.get_rate_limit_stats()


@app.post("/ab-test/create")
async def create_ab_test(
    test_request: ABTestRequest,
    tier: str = Depends(verify_api_key)
):
    """Create a new A/B test"""
    router = get_router()
    
    if not router.ab_testing:
        raise HTTPException(status_code=503, detail="A/B testing not enabled")
    
    # Parse variants
    variants = []
    for v in test_request.variants:
        variants.append(Variant(**v))
    
    try:
        test_id = router.ab_testing.create_test(
            test_name=test_request.test_name,
            variants=variants,
            duration=test_request.duration,
            min_samples=test_request.min_samples
        )
        
        return {"test_id": test_id, "message": "A/B test created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ab-test/{test_id}/status")
async def get_ab_test_status(
    test_id: str,
    tier: str = Depends(verify_api_key)
):
    """Get A/B test status"""
    router = get_router()
    
    if not router.ab_testing:
        raise HTTPException(status_code=503, detail="A/B testing not enabled")
    
    status = router.ab_testing.get_test_status(test_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return status


@app.get("/ab-test/{test_id}/report")
async def get_ab_test_report(
    test_id: str,
    tier: str = Depends(verify_api_key)
):
    """Get A/B test report"""
    router = get_router()
    
    if not router.ab_testing:
        raise HTTPException(status_code=503, detail="A/B testing not enabled")
    
    report = router.ab_testing.generate_report(test_id)
    
    return {"report": report}


@app.get("/ab-test/active")
async def get_active_tests(tier: str = Depends(verify_api_key)):
    """Get all active A/B tests"""
    router = get_router()
    
    if not router.ab_testing:
        raise HTTPException(status_code=503, detail="A/B testing not enabled")
    
    tests = router.ab_testing.get_all_active_tests()
    
    return {"active_tests": tests}


@app.post("/ab-test/{test_id}/stop")
async def stop_ab_test(
    test_id: str,
    tier: str = Depends(verify_api_key)
):
    """Stop an A/B test"""
    router = get_router()
    
    if not router.ab_testing:
        raise HTTPException(status_code=503, detail="A/B testing not enabled")
    
    router.ab_testing.stop_test(test_id)
    
    return {"message": "Test stopped successfully"}


@app.post("/classify")
async def classify_query(
    query: str,
    tier: str = Depends(verify_api_key)
):
    """Classify a query without processing it"""
    router = get_router()
    classification = router.classify_query_only(query)
    
    return {
        "query": query,
        "classification": classification,
        "tier_mapping": {
            "S": "tier1",
            "M": "tier2",
            "A": "tier3"
        }[classification]
    }


@app.post("/cache/check")
async def check_cache(
    query: str,
    tier: str = Depends(verify_api_key)
):
    """Check if query exists in cache"""
    router = get_router()
    cached = router.check_cache(query)
    
    return {
        "query": query,
        "in_cache": cached is not None,
        "cached_response": cached if cached else None
    }


@app.delete("/cache/clear")
async def clear_cache(tier: str = Depends(verify_api_key)):
    """Clear all cached responses (admin only)"""
    if tier != "enterprise":
        raise HTTPException(status_code=403, detail="Enterprise tier required")
    
    router = get_router()
    router.clear_cache()
    
    return {"message": "Cache cleared successfully"}


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("\n" + "="*80)
    print("🚀 Starting Dynamic LLM Router API Server")
    print("="*80)
    
    # Initialize router
    router = get_router()
    print("✅ Router initialized with professional features")
    print(f"   - Monitoring: {router.enable_monitoring}")
    print(f"   - Rate Limiting: {router.enable_rate_limiting}")
    print(f"   - Quality Eval: {router.enable_quality_eval}")
    print(f"   - A/B Testing: {router.enable_ab_testing}")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("="*80 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n" + "="*80)
    print("🛑 Shutting down API server")
    print("="*80 + "\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the API server"""
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
