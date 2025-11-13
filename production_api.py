"""Production FastAPI Backend for LLM Router System"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file FIRST
load_dotenv()

# Debug: Print loaded SECRET_KEY (first 10 chars only for security)
secret_key = os.getenv("SECRET_KEY", "NOT_LOADED")
print(f"🔑 SECRET_KEY loaded: {secret_key[:10]}..." if len(secret_key) > 10 else f"❌ SECRET_KEY: {secret_key}")

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import database
import schemas
import crud
import auth
from main2 import DynamicLLMRouter
from prompt_improver import PromptImprover
from conversation_cache import CacheManager

# Initialize database
database.init_db()

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic LLM Router API",
    description="Production API for intelligent LLM query routing",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج، استبدلها بالدومينات المحددة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
# Disable professional features to avoid blocking
router_system = DynamicLLMRouter(
    enable_logging=True,
    enable_monitoring=False,  # Disable to avoid delays
    enable_rate_limiting=False,
    enable_quality_eval=False,
    enable_ab_testing=False
)
prompt_improver = PromptImprover()


# ==================== AUTHENTICATION ENDPOINTS ====================
@app.post("/api/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Register new user"""
    
    # Check if user exists
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    db_user = crud.create_user(db, user)
    return db_user


@app.post("/api/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    """Login and get JWT token"""
    
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token (sub must be a string per JWT spec)
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_current_user_info(
    current_user: database.User = Depends(auth.get_current_user)
):
    """Get current user info"""
    return current_user


# ==================== API KEY MANAGEMENT ====================
@app.post("/api/keys", response_model=schemas.APIKeyResponse, status_code=status.HTTP_201_CREATED)
def add_api_key(
    key_data: schemas.APIKeyCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Add user's own API key"""
    
    if current_user.api_key_source != database.APIKeySource.USER_PROVIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is configured to use system-provided API keys"
        )
    
    db_key = crud.create_user_api_key(db, current_user.id, key_data)
    return db_key


@app.get("/api/keys", response_model=List[schemas.APIKeyResponse])
def get_user_api_keys(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get user's API keys"""
    return crud.get_user_api_keys(db, current_user.id)


@app.delete("/api/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Delete API key"""
    
    success = crud.delete_user_api_key(db, key_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )


# ==================== QUERY ENDPOINTS ====================
@app.post("/api/query", response_model=schemas.QueryResponse)
async def process_query(
    query_request: schemas.QueryRequest,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Process a single query"""
    
    # Get user's custom models and prepend them to each tier
    user_models = crud.get_user_models_by_tier(db, current_user.id)
    
    # Check usage limits
    if current_user.api_key_source == database.APIKeySource.SYSTEM_PROVIDED:
        if current_user.queries_used_this_month >= current_user.monthly_query_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly query limit reached. Please upgrade your plan or add your own API keys."
            )
    
    # Process query - run in thread pool to avoid blocking
    start_time = time.time()
    
    print(f"[API] Starting query processing: {query_request.query[:50]}...")
    
    try:
        # Run blocking operation in thread pool with timeout (60 seconds)
        loop = asyncio.get_event_loop()
        print(f"[API] Creating thread pool executor...")
        
        with ThreadPoolExecutor(max_workers=1) as pool:
            print(f"[API] Submitting query to thread pool...")
            # Use lambda to pass user_models
            future = loop.run_in_executor(
                pool, 
                lambda: router_system.process_query(query_request.query, user_models=user_models)
            )
            print(f"[API] Waiting for result (max 60s)...")
            result = await asyncio.wait_for(future, timeout=60.0)
        
        processing_time = time.time() - start_time
        print(f"[API] Got result from router! Time: {processing_time:.2f}s")
        
    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        print(f"[API] TIMEOUT after {processing_time:.2f}s!")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Query processing timeout (60s). Please try a simpler query or try again later."
        )
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"[API] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing error: {str(e)}"
        )
    
    # Log query
    # Handle None values for cache hits before logging
    classification = result.classification or "cached"
    model_tier = result.model_tier or "cache"
    used_model = result.used_model or "semantic_cache"
    cost = 0.0 if result.cache_hit else 0.001
    
    query_log = crud.create_query_log(
        db=db,
        user_id=current_user.id,
        query_data={
            "query": result.query,
            "response": result.response,
            "classification": classification,
            "model_tier": model_tier,
            "used_model": used_model,
            "cache_hit": result.cache_hit,
            "processing_time": processing_time,
            "estimated_cost": cost,
            "success": result.success,
            "error_message": result.error
        }
    )
    
    # Handle None values for cache hits
    # When cache hit occurs, classification/tier/model are None
    print(f"[API] Creating response object...")
    response_obj = schemas.QueryResponse(
        id=query_log.id,
        success=result.success,
        query=result.query,
        response=result.response,
        classification=result.classification or "cached",
        model_tier=result.model_tier or "cache",
        used_model=result.used_model or "semantic_cache",
        cache_hit=result.cache_hit,
        processing_time=processing_time,
        estimated_cost=0.0 if result.cache_hit else 0.001,  # Cache hits are free
        created_at=query_log.created_at,
        error_message=result.error
    )
    print(f"[API] Returning response to frontend!")
    return response_obj


@app.post("/api/query/batch", response_model=schemas.BatchQueryResponse)
async def process_batch_queries(
    batch_request: schemas.BatchQueryRequest,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Process multiple queries in batch"""
    
    # Get user's custom models
    user_models = crud.get_user_models_by_tier(db, current_user.id)
    
    # Check limits
    if current_user.api_key_source == database.APIKeySource.SYSTEM_PROVIDED:
        remaining = current_user.monthly_query_limit - current_user.queries_used_this_month
        if len(batch_request.queries) > remaining:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Batch size exceeds remaining queries. You have {remaining} queries left."
            )
    
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    total_time = 0
    total_cost = 0
    successful = 0
    failed = 0
    
    loop = asyncio.get_event_loop()
    
    for query_text in batch_request.queries:
        start = time.time()
        
        # Run in thread pool with user models
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool, 
                lambda qt=query_text: router_system.process_query(qt, user_models=user_models)
            )
        
        proc_time = time.time() - start
        total_time += proc_time
        
        # Handle None values for cache hits
        classification = result.classification or "cached"
        model_tier = result.model_tier or "cache"
        used_model = result.used_model or "semantic_cache"
        cost = 0.0 if result.cache_hit else 0.001
        
        # Log each query
        query_log = crud.create_query_log(
            db=db,
            user_id=current_user.id,
            query_data={
                "query": query_text,
                "response": result.response,
                "classification": classification,
                "model_tier": model_tier,
                "used_model": used_model,
                "cache_hit": result.cache_hit,
                "processing_time": proc_time,
                "estimated_cost": cost,
                "success": result.success,
                "error_message": result.error
            }
        )
        
        if result.success:
            successful += 1
        else:
            failed += 1
        
        # Add cost to total (already calculated above)
        total_cost += cost
        
        results.append(schemas.QueryResponse(
            id=query_log.id,
            success=result.success,
            query=result.query,
            response=result.response,
            classification=classification,
            model_tier=model_tier,
            used_model=used_model,
            cache_hit=result.cache_hit,
            processing_time=proc_time,
            estimated_cost=cost,
            created_at=query_log.created_at,
            error_message=result.error
        ))
    
    return schemas.BatchQueryResponse(
        total_queries=len(batch_request.queries),
        successful=successful,
        failed=failed,
        results=results,
        total_processing_time=total_time,
        total_cost=total_cost
    )


@app.get("/api/queries", response_model=List[schemas.QueryResponse])
def get_query_history(
    limit: int = 50,
    offset: int = 0,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get user's query history"""
    
    queries = crud.get_user_queries(db, current_user.id, limit, offset)
    
    return [
        schemas.QueryResponse(
            id=q.id,
            success=q.success,
            query=q.query_text,
            response=q.response_text or "",
            classification=q.classification or "Unknown",
            model_tier=q.model_tier or "tier1",
            used_model=q.used_model or "Unknown",
            cache_hit=q.cache_hit,
            processing_time=q.processing_time or 0.0,
            estimated_cost=q.estimated_cost,
            created_at=q.created_at,
            error_message=q.error_message
        )
        for q in queries
    ]


# ==================== PROMPT SUGGESTIONS ====================
@app.post("/api/prompt/suggest", response_model=schemas.PromptSuggestionResponse)
def suggest_better_prompt(
    request: schemas.PromptSuggestionRequest,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get suggestions for improving unclear prompts"""
    
    result = prompt_improver.generate_suggestions(request.prompt)
    
    # Save suggestion
    if not result["is_clear"]:
        crud.create_prompt_suggestion(
            db,
            current_user.id,
            request.prompt,
            result["suggestions"]
        )
    
    return schemas.PromptSuggestionResponse(
        original_prompt=result["original_prompt"],
        is_clear=result["is_clear"],
        suggestions=result["suggestions"],
        explanation=result["explanation"]
    )


@app.post("/api/prompt/classify", response_model=schemas.ClassificationPreview)
def classify_prompt(
    request: schemas.PromptSuggestionRequest,
    current_user: database.User = Depends(auth.get_current_user)
):
    """Preview classification without processing"""
    
    classification = router_system.classify_query_only(request.prompt)
    
    tier_map = {"S": "tier1", "M": "tier2", "A": "tier3"}
    cost_map = {"S": 0.0002, "M": 0.002, "A": 0.03}
    time_map = {"S": 1.2, "M": 2.1, "A": 3.5}
    
    return schemas.ClassificationPreview(
        query=request.prompt,
        classification=classification,
        recommended_tier=tier_map.get(classification, "tier1"),
        estimated_cost=cost_map.get(classification, 0.001),
        estimated_time=time_map.get(classification, 2.0)
    )


# ==================== FEEDBACK ENDPOINTS ====================
@app.post("/api/feedback", response_model=schemas.FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback: schemas.FeedbackCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Submit feedback for a query"""
    
    # Verify query belongs to user
    query = crud.get_query_by_id(db, feedback.query_id, current_user.id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    # Check if feedback already exists
    existing = crud.get_feedback_by_query(db, feedback.query_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback already submitted for this query"
        )
    
    db_feedback = crud.create_feedback(db, current_user.id, feedback)
    return db_feedback


# ==================== STATISTICS ENDPOINTS ====================
@app.get("/api/stats/user", response_model=schemas.UserStats)
def get_user_statistics(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get user's statistics"""
    return crud.get_user_stats(db, current_user.id)


@app.get("/api/stats/system", response_model=schemas.SystemStats)
def get_system_statistics(
    current_user: database.User = Depends(auth.get_current_admin),
    db: Session = Depends(database.get_db)
):
    """Get system-wide statistics (admin only)"""
    return crud.get_system_stats(db)


@app.get("/api/stats/feedback")
def get_feedback_statistics(
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get feedback statistics by model"""
    from sqlalchemy import func
    
    # Get feedback stats grouped by model
    feedback_stats = db.query(
        database.QueryLog.used_model,
        database.Feedback.rating,
        func.count(database.Feedback.id).label('count')
    ).join(
        database.Feedback, database.QueryLog.id == database.Feedback.query_id
    ).filter(
        database.QueryLog.user_id == current_user.id
    ).group_by(
        database.QueryLog.used_model,
        database.Feedback.rating
    ).all()
    
    # Organize by model
    model_stats = {}
    for model, rating, count in feedback_stats:
        if model not in model_stats:
            model_stats[model] = {
                'excellent': 0,
                'good': 0,
                'average': 0,
                'poor': 0,
                'very_poor': 0,
                'total': 0
            }
        rating_str = rating.value if hasattr(rating, 'value') else str(rating)
        model_stats[model][rating_str] = count
        model_stats[model]['total'] += count
    
    # Calculate average scores
    for model in model_stats:
        stats = model_stats[model]
        score_map = {'excellent': 5, 'good': 4, 'average': 3, 'poor': 2, 'very_poor': 1}
        total_score = sum(stats[rating] * score_map[rating] for rating in score_map)
        stats['average_score'] = total_score / stats['total'] if stats['total'] > 0 else 0
    
    return {
        'model_stats': model_stats,
        'total_feedbacks': sum(s['total'] for s in model_stats.values())
    }


# ==================== CONVERSATION ENDPOINTS ====================
@app.post("/api/conversations", response_model=schemas.ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: schemas.ConversationCreate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Create new conversation"""
    db_conversation = crud.create_conversation(
        db=db,
        user_id=current_user.id,
        title=conversation.title
    )
    return db_conversation


@app.get("/api/conversations", response_model=List[schemas.ConversationListItem])
def get_conversations(
    limit: int = 50,
    offset: int = 0,
    active_only: bool = True,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get user's conversations"""
    conversations = crud.get_user_conversations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        active_only=active_only
    )
    
    # Add message count to each conversation
    result = []
    for conv in conversations:
        result.append(schemas.ConversationListItem(
            id=conv.id,
            title=conv.title,
            is_active=conv.is_active,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages)
        ))
    
    return result


@app.get("/api/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get specific conversation with messages"""
    conversation = crud.get_conversation_by_id(db, conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@app.put("/api/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
def update_conversation(
    conversation_id: int,
    conversation_update: schemas.ConversationUpdate,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Update conversation"""
    updated_conv = crud.update_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=conversation_update.title
    )
    
    if not updated_conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return updated_conv


@app.delete("/api/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Delete conversation"""
    success = crud.delete_conversation(db, conversation_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Clear cache for this conversation
    CacheManager.clear_cache(conversation_id)


@app.post("/api/conversations/{conversation_id}/messages", response_model=schemas.QueryResponse)
async def send_message(
    conversation_id: int,
    query_request: schemas.QueryRequest,
    current_user: database.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Send message in a conversation"""
    
    # Get user's custom models
    user_models = crud.get_user_models_by_tier(db, current_user.id)
    
    # Verify conversation exists and belongs to user
    conversation = crud.get_conversation_by_id(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Check usage limits
    if current_user.api_key_source == database.APIKeySource.SYSTEM_PROVIDED:
        if current_user.queries_used_this_month >= current_user.monthly_query_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly query limit reached. Please upgrade your plan or add your own API keys."
            )
    
    # Get conversation cache
    conv_cache = CacheManager.get_cache(conversation_id)
    
    # Check cache first (if not skipping)
    cached_response = None
    if not query_request.skip_cache:
        cached_response = conv_cache.get(query_request.query)
    
    start_time = time.time()
    
    if cached_response:
        # Cache hit
        processing_time = time.time() - start_time
        
        # Create user message
        crud.create_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=query_request.query
        )
        
        # Create assistant message
        crud.create_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=cached_response,
            message_metadata={
                "cache_hit": True,
                "classification": "cached",
                "model_tier": "cache",
                "used_model": "semantic_cache"
            }
        )
        
        # Log query
        query_log = crud.create_query_log(
            db=db,
            user_id=current_user.id,
            query_data={
                "query": query_request.query,
                "response": cached_response,
                "classification": "cached",
                "model_tier": "cache",
                "used_model": "semantic_cache",
                "cache_hit": True,
                "processing_time": processing_time,
                "estimated_cost": 0.0,
                "success": True,
                "error_message": None
            }
        )
        
        return schemas.QueryResponse(
            id=query_log.id,
            success=True,
            query=query_request.query,
            response=cached_response,
            classification="cached",
            model_tier="cache",
            used_model="semantic_cache",
            cache_hit=True,
            processing_time=processing_time,
            estimated_cost=0.0,
            created_at=query_log.created_at,
            error_message=None
        )
    
    # Process query with router (with user models)
    try:
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = loop.run_in_executor(
                pool, 
                lambda: router_system.process_query(query_request.query, user_models=user_models)
            )
            result = await asyncio.wait_for(future, timeout=60.0)
        
        processing_time = time.time() - start_time
        
    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Query processing timeout (60s). Please try a simpler query or try again later."
        )
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing error: {str(e)}"
        )
    
    # Save to conversation cache
    conv_cache.set(query_request.query, result.response)
    
    # Create user message
    crud.create_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=query_request.query
    )
    
    # Log query
    classification = result.classification or "cached"
    model_tier = result.model_tier or "cache"
    used_model = result.used_model or "semantic_cache"
    cost = 0.0 if result.cache_hit else 0.001
    
    query_log = crud.create_query_log(
        db=db,
        user_id=current_user.id,
        query_data={
            "query": result.query,
            "response": result.response,
            "classification": classification,
            "model_tier": model_tier,
            "used_model": used_model,
            "cache_hit": result.cache_hit,
            "processing_time": processing_time,
            "estimated_cost": cost,
            "success": result.success,
            "error_message": result.error
        }
    )
    
    # Create assistant message
    crud.create_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=result.response,
        query_id=query_log.id,
        message_metadata={
            "classification": classification,
            "model_tier": model_tier,
            "used_model": used_model,
            "cache_hit": result.cache_hit,
            "processing_time": processing_time,
            "estimated_cost": cost
        }
    )
    
    return schemas.QueryResponse(
        id=query_log.id,
        success=result.success,
        query=result.query,
        response=result.response,
        classification=classification,
        model_tier=model_tier,
        used_model=used_model,
        cache_hit=result.cache_hit,
        processing_time=processing_time,
        estimated_cost=cost,
        created_at=query_log.created_at,
        error_message=result.error
    )


# ==================== HEALTH CHECK ====================
@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "router_initialized": router_system is not None
    }


# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Dynamic LLM Router API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
