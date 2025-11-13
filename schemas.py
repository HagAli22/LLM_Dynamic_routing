"""Pydantic Schemas for API Request/Response Validation"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================
class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    ENTERPRISE = "enterprise"


class APIKeySourceEnum(str, Enum):
    SYSTEM_PROVIDED = "system_provided"
    USER_PROVIDED = "user_provided"


class FeedbackRatingEnum(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    VERY_POOR = "very_poor"


# ==================== USER SCHEMAS ====================
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    company: Optional[str] = None
    api_key_source: APIKeySourceEnum = APIKeySourceEnum.SYSTEM_PROVIDED


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    company: Optional[str]
    role: str
    api_key_source: str
    is_active: bool
    monthly_query_limit: int
    queries_used_this_month: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== API KEY SCHEMAS ====================
class APIKeyCreate(BaseModel):
    provider: str = Field(..., description="Provider name (openai, anthropic, etc.)")
    api_key: str = Field(..., description="The actual API key")
    key_name: Optional[str] = None
    model_name: Optional[str] = Field(None, description="Model display name (e.g., qwen-2.5-72b-instruct)")
    model_path: Optional[str] = Field(None, description="Full model path (e.g., qwen/qwen-2.5-72b-instruct:free)")
    tier: str = Field("tier1", description="Tier for this model (tier1, tier2, tier3)")


class APIKeyResponse(BaseModel):
    id: int
    provider: str
    key_name: Optional[str]
    model_name: Optional[str]
    model_path: Optional[str]
    tier: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== QUERY SCHEMAS ====================
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The user's query")
    force_tier: Optional[str] = Field(None, description="Force specific tier (tier1/tier2/tier3)")
    skip_cache: bool = Field(False, description="Skip semantic cache")


class BatchQueryRequest(BaseModel):
    queries: List[str] = Field(..., min_items=1, max_items=100)
    skip_cache: bool = False


class QueryResponse(BaseModel):
    id: int
    success: bool
    query: str
    response: str
    classification: str
    model_tier: str
    used_model: str
    cache_hit: bool
    processing_time: float
    estimated_cost: float
    created_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class BatchQueryResponse(BaseModel):
    total_queries: int
    successful: int
    failed: int
    results: List[QueryResponse]
    total_processing_time: float
    total_cost: float


# ==================== FEEDBACK SCHEMAS ====================
class FeedbackCreate(BaseModel):
    query_id: int
    rating: FeedbackRatingEnum
    comment: Optional[str] = None
    classification_correct: Optional[bool] = None
    model_appropriate: Optional[bool] = None
    response_helpful: Optional[bool] = None
    response_accurate: Optional[bool] = None
    response_fast_enough: Optional[bool] = None


class FeedbackResponse(BaseModel):
    id: int
    query_id: int
    rating: str
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PROMPT SUGGESTION SCHEMAS ====================
class PromptSuggestionRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class PromptSuggestionResponse(BaseModel):
    original_prompt: str
    is_clear: bool
    suggestions: List[str]
    explanation: str


class PromptSuggestionAccept(BaseModel):
    suggestion_id: int
    selected_suggestion: str


# ==================== STATISTICS SCHEMAS ====================
class UserStats(BaseModel):
    total_queries: int
    queries_this_month: int
    queries_remaining: int
    average_processing_time: float
    cache_hit_rate: float
    total_cost: float
    queries_by_tier: Dict[str, int]
    queries_by_classification: Dict[str, int]
    average_rating: Optional[float]


class SystemStats(BaseModel):
    total_users: int
    total_queries_today: int
    total_queries_all_time: int
    average_queries_per_user: float
    cache_hit_rate: float
    total_cost_today: float
    total_cost_all_time: float
    queries_by_tier: Dict[str, int]
    average_rating: Optional[float]


# ==================== CLASSIFICATION PREVIEW ====================
class ClassificationPreview(BaseModel):
    query: str
    classification: str
    recommended_tier: str
    estimated_cost: float
    estimated_time: float


# ==================== CONVERSATION SCHEMAS ====================
class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    message_metadata: Optional[Dict[str, Any]] = None
    query_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: int
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True


# ==================== MODEL RATING SCHEMAS ====================
class ModelFeedbackCreate(BaseModel):
    query_id: int
    model_identifier: str
    feedback_type: str = Field(..., description="like, dislike, or star")
    comment: Optional[str] = None


class ModelFeedbackResponse(BaseModel):
    success: bool
    model_identifier: str
    feedback_type: str
    points_change: int
    new_score: int
    total_feedbacks: int


class ModelRatingStats(BaseModel):
    model_identifier: str
    model_name: str
    tier: str
    score: int
    total_likes: int
    total_dislikes: int
    total_stars: int
    total_feedbacks: int
    total_uses: int
    successful_uses: int
    failed_uses: int
    success_rate: float
    avg_response_time: float
    avg_cost: float
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True
