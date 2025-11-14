"""CRUD Operations for Database Models"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import database
import schemas
from auth import get_password_hash, encrypt_api_key, decrypt_api_key


# ==================== USER OPERATIONS ====================
def create_user(db: Session, user: schemas.UserCreate) -> database.User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    
    db_user = database.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        company=user.company,
        api_key_source=database.APIKeySource(user.api_key_source.value)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(db: Session, user_id: int) -> Optional[database.User]:
    """Get user by ID"""
    return db.query(database.User).filter(database.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[database.User]:
    """Get user by username"""
    return db.query(database.User).filter(database.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[database.User]:
    """Get user by email"""
    return db.query(database.User).filter(database.User.email == email).first()


# ==================== API KEY OPERATIONS ====================
def create_user_api_key(
    db: Session,
    user_id: int,
    api_key_data: schemas.APIKeyCreate
) -> database.UserAPIKey:
    """Create user API key and initialize model rating"""
    encrypted = encrypt_api_key(api_key_data.api_key)
    
    db_key = database.UserAPIKey(
        user_id=user_id,
        provider=api_key_data.provider,
        encrypted_key=encrypted,
        key_name=api_key_data.key_name,
        model_name=api_key_data.model_name,
        tier=api_key_data.tier,
        input_price=api_key_data.input_price,
        output_price=api_key_data.output_price
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    # إنشاء سجل تقييم للموديل الجديد
    _initialize_user_model_rating(db, api_key_data.model_name, api_key_data.tier)
    
    # إضافة السعر للـ PRICES dictionary
    _add_model_price(api_key_data.model_name, api_key_data.input_price, api_key_data.output_price)
    
    return db_key


def _initialize_user_model_rating(db: Session, model_name: str, tier: str):
    """تهيئة تقييم الموديل الجديد بنفس نقاط أعلى موديل في الـ tier"""
    from model_rating_system import ModelRatingManager
    
    # التحقق من وجود الموديل
    existing = db.query(database.ModelRating).filter(
        database.ModelRating.model_identifier == model_name
    ).first()
    
    if existing:
        return  # الموديل موجود بالفعل
    
    # الحصول على أعلى نقاط في الـ tier
    top_model = db.query(database.ModelRating).filter(
        database.ModelRating.tier == tier
    ).order_by(database.ModelRating.score.desc()).first()
    
    initial_score = top_model.score + 1 if top_model else 101
    
    # إنشاء سجل جديد
    new_rating = database.ModelRating(
        model_identifier=model_name,
        model_name=model_name.split('/')[-1].replace(':free', ''),
        tier=tier,
        score=initial_score
    )
    
    db.add(new_rating)
    db.commit()
    print(f"✅ Initialized model rating: {model_name} with {initial_score} points in {tier} (as #1 in tier)")


def _add_model_price(model_name: str, input_price: float, output_price: float):
    """إضافة سعر الموديل للـ PRICES dictionary"""
    from fallback import PRICES
    
    PRICES[model_name] = {
        "input": input_price,
        "output": output_price
    }
    print(f"✅ Added pricing for {model_name}: input={input_price}, output={output_price}")


def get_user_api_keys(db: Session, user_id: int) -> List[database.UserAPIKey]:
    """Get all API keys for a user"""
    return db.query(database.UserAPIKey).filter(
        database.UserAPIKey.user_id == user_id,
        database.UserAPIKey.is_active == True
    ).all()


def get_user_models_by_tier(db: Session, user_id: int) -> Dict[str, List]:
    """Get user's custom models organized by tier with API keys"""
    user_keys = get_user_api_keys(db, user_id)
    
    # Organize by tier
    models_by_tier = {
        "tier1": [],
        "tier2": [],
        "tier3": []
    }
    
    for key in user_keys:
        if not key.is_active:
            continue
            
        # model_path: full path for API call (e.g., qwen/qwen-2.5-72b-instruct:free)
        # model_name: display name and env variable name (e.g., qwen-2.5-72b-instruct)
        model_path = key.model_path or key.model_name
        
        if model_path and key.tier in models_by_tier:
            # Decrypt API key
            try:
                decrypted_key = decrypt_api_key(key.encrypted_key)
            except:
                continue  # Skip if decryption fails
            
            models_by_tier[key.tier].append({
                "model_path": model_path,  # للاستدعاء في client.chat.completions.create
                "env_var_name": key.model_name,  # اسم المتغير (للمستقبل)
                "api_key": decrypted_key,  # المفتاح الفعلي
                "provider": key.provider,
                "key_id": key.id
            })
    
    return models_by_tier


def delete_user_api_key(db: Session, key_id: int, user_id: int) -> bool:
    """Delete user API key and remove from rating system"""
    key = db.query(database.UserAPIKey).filter(
        database.UserAPIKey.id == key_id,
        database.UserAPIKey.user_id == user_id
    ).first()
    
    if key:
        model_name = key.model_name
        
        # Delete API key
        db.delete(key)
        
        # Also remove model from rating system
        model_rating = db.query(database.ModelRating).filter(
            database.ModelRating.model_identifier == model_name
        ).first()
        
        if model_rating:
            db.delete(model_rating)
            print(f"🗑️ Removed model {model_name} from rating system")
        
        db.commit()
        print(f"✅ Deleted API key and model rating: {model_name}")
        return True
    return False


# ==================== QUERY LOG OPERATIONS ====================
def create_query_log(
    db: Session,
    user_id: int,
    query_data: dict
) -> database.QueryLog:
    """Create query log entry"""
    db_log = database.QueryLog(
        user_id=user_id,
        query_text=query_data.get("query"),
        response_text=query_data.get("response"),
        classification=query_data.get("classification"),
        model_tier=query_data.get("model_tier"),
        used_model=query_data.get("used_model"),
        cache_hit=query_data.get("cache_hit", False),
        processing_time=query_data.get("processing_time"),
        estimated_cost=query_data.get("estimated_cost", 0.0),
        success=query_data.get("success", True),
        error_message=query_data.get("error_message"),
        query_metadata=query_data.get("metadata")
    )
    
    db.add(db_log)
    
    # Update user's monthly query count
    user = db.query(database.User).filter(database.User.id == user_id).first()
    if user:
        user.queries_used_this_month += 1
    
    db.commit()
    db.refresh(db_log)
    return db_log


def get_user_queries(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[database.QueryLog]:
    """Get user's query history"""
    return db.query(database.QueryLog).filter(
        database.QueryLog.user_id == user_id
    ).order_by(database.QueryLog.created_at.desc()).offset(offset).limit(limit).all()


def get_query_by_id(db: Session, query_id: int, user_id: int) -> Optional[database.QueryLog]:
    """Get specific query by ID"""
    return db.query(database.QueryLog).filter(
        database.QueryLog.id == query_id,
        database.QueryLog.user_id == user_id
    ).first()


# ==================== FEEDBACK OPERATIONS ====================
def create_feedback(
    db: Session,
    user_id: int,
    feedback_data: schemas.FeedbackCreate
) -> database.Feedback:
    """Create feedback for a query"""
    db_feedback = database.Feedback(
        user_id=user_id,
        query_id=feedback_data.query_id,
        rating=database.FeedbackRating(feedback_data.rating.value),
        comment=feedback_data.comment,
        classification_correct=feedback_data.classification_correct,
        model_appropriate=feedback_data.model_appropriate,
        response_helpful=feedback_data.response_helpful,
        response_accurate=feedback_data.response_accurate,
        response_fast_enough=feedback_data.response_fast_enough
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


def get_feedback_by_query(db: Session, query_id: int) -> Optional[database.Feedback]:
    """Get feedback for a specific query"""
    return db.query(database.Feedback).filter(
        database.Feedback.query_id == query_id
    ).first()


# ==================== PROMPT SUGGESTION OPERATIONS ====================
def create_prompt_suggestion(
    db: Session,
    user_id: int,
    original_prompt: str,
    suggestions: List[str]
) -> database.PromptSuggestion:
    """Create prompt suggestion record"""
    db_suggestion = database.PromptSuggestion(
        user_id=user_id,
        original_prompt=original_prompt,
        suggested_prompts=suggestions
    )
    
    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)
    return db_suggestion


def accept_prompt_suggestion(
    db: Session,
    suggestion_id: int,
    selected: str
) -> bool:
    """Mark a suggestion as accepted"""
    suggestion = db.query(database.PromptSuggestion).filter(
        database.PromptSuggestion.id == suggestion_id
    ).first()
    
    if suggestion:
        suggestion.accepted = True
        suggestion.selected_suggestion = selected
        db.commit()
        return True
    return False


# ==================== STATISTICS OPERATIONS ====================
def get_user_stats(db: Session, user_id: int) -> dict:
    """Get user statistics"""
    user = db.query(database.User).filter(database.User.id == user_id).first()
    
    total_queries = db.query(func.count(database.QueryLog.id)).filter(
        database.QueryLog.user_id == user_id
    ).scalar()
    
    # Queries this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    queries_this_month = db.query(func.count(database.QueryLog.id)).filter(
        database.QueryLog.user_id == user_id,
        database.QueryLog.created_at >= start_of_month
    ).scalar()
    
    # Average processing time
    avg_time = db.query(func.avg(database.QueryLog.processing_time)).filter(
        database.QueryLog.user_id == user_id
    ).scalar() or 0.0
    
    # Cache hit rate
    total = total_queries or 1
    cache_hits = db.query(func.count(database.QueryLog.id)).filter(
        database.QueryLog.user_id == user_id,
        database.QueryLog.cache_hit == True
    ).scalar()
    
    # Total cost
    total_cost = db.query(func.sum(database.QueryLog.estimated_cost)).filter(
        database.QueryLog.user_id == user_id
    ).scalar() or 0.0
    
    # Queries by tier
    queries_by_tier = {}
    for tier in ["tier1", "tier2", "tier3"]:
        count = db.query(func.count(database.QueryLog.id)).filter(
            database.QueryLog.user_id == user_id,
            database.QueryLog.model_tier == tier
        ).scalar()
        queries_by_tier[tier] = count
    
    # Queries by classification
    queries_by_class = {}
    for cls in ["S", "M", "A"]:
        count = db.query(func.count(database.QueryLog.id)).filter(
            database.QueryLog.user_id == user_id,
            database.QueryLog.classification == cls
        ).scalar()
        queries_by_class[cls] = count
    
    # Average rating
    avg_rating = db.query(func.avg(
        case(
            (database.Feedback.rating == database.FeedbackRating.EXCELLENT, 5),
            (database.Feedback.rating == database.FeedbackRating.GOOD, 4),
            (database.Feedback.rating == database.FeedbackRating.AVERAGE, 3),
            (database.Feedback.rating == database.FeedbackRating.POOR, 2),
            (database.Feedback.rating == database.FeedbackRating.VERY_POOR, 1),
            else_=None
        )
    )).filter(database.Feedback.user_id == user_id).scalar()
    
    return {
        "total_queries": total_queries,
        "queries_this_month": queries_this_month,
        "queries_remaining": user.monthly_query_limit - queries_this_month,
        "average_processing_time": float(avg_time),
        "cache_hit_rate": cache_hits / total,
        "total_cost": float(total_cost),
        "queries_by_tier": queries_by_tier,
        "queries_by_classification": queries_by_class,
        "average_rating": float(avg_rating) if avg_rating else None
    }


def get_system_stats(db: Session) -> dict:
    """Get system-wide statistics"""
    total_users = db.query(func.count(database.User.id)).scalar()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    queries_today = db.query(func.count(database.QueryLog.id)).filter(
        database.QueryLog.created_at >= today_start
    ).scalar()
    
    total_queries = db.query(func.count(database.QueryLog.id)).scalar()
    
    cache_hits = db.query(func.count(database.QueryLog.id)).filter(
        database.QueryLog.cache_hit == True
    ).scalar()
    
    cost_today = db.query(func.sum(database.QueryLog.estimated_cost)).filter(
        database.QueryLog.created_at >= today_start
    ).scalar() or 0.0
    
    total_cost = db.query(func.sum(database.QueryLog.estimated_cost)).scalar() or 0.0
    
    # Queries by tier
    queries_by_tier = {}
    for tier in ["tier1", "tier2", "tier3"]:
        count = db.query(func.count(database.QueryLog.id)).filter(
            database.QueryLog.model_tier == tier
        ).scalar()
        queries_by_tier[tier] = count
    
    return {
        "total_users": total_users,
        "total_queries_today": queries_today,
        "total_queries_all_time": total_queries,
        "average_queries_per_user": total_queries / total_users if total_users > 0 else 0,
        "cache_hit_rate": cache_hits / total_queries if total_queries > 0 else 0,
        "total_cost_today": float(cost_today),
        "total_cost_all_time": float(total_cost),
        "queries_by_tier": queries_by_tier,
        "average_rating": None
    }


# ==================== CONVERSATION OPERATIONS ====================
def create_conversation(
    db: Session,
    user_id: int,
    title: str
) -> database.Conversation:
    """Create new conversation"""
    db_conversation = database.Conversation(
        user_id=user_id,
        title=title,
        cache_file=f"cache/conversation_{user_id}_{datetime.utcnow().timestamp()}.json"
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_user_conversations(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    active_only: bool = True
) -> List[database.Conversation]:
    """Get user's conversations"""
    query = db.query(database.Conversation).filter(
        database.Conversation.user_id == user_id
    )
    
    if active_only:
        query = query.filter(database.Conversation.is_active == True)
    
    return query.order_by(
        database.Conversation.updated_at.desc()
    ).offset(offset).limit(limit).all()


def get_conversation_by_id(
    db: Session,
    conversation_id: int,
    user_id: int
) -> Optional[database.Conversation]:
    """Get specific conversation by ID"""
    return db.query(database.Conversation).filter(
        database.Conversation.id == conversation_id,
        database.Conversation.user_id == user_id
    ).first()


def update_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
    title: Optional[str] = None
) -> Optional[database.Conversation]:
    """Update conversation"""
    conversation = get_conversation_by_id(db, conversation_id, user_id)
    
    if not conversation:
        return None
    
    if title is not None:
        conversation.title = title
    
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(
    db: Session,
    conversation_id: int,
    user_id: int
) -> bool:
    """Delete (deactivate) conversation"""
    conversation = get_conversation_by_id(db, conversation_id, user_id)
    
    if not conversation:
        return False
    
    conversation.is_active = False
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    return True


def create_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    query_id: Optional[int] = None,
    message_metadata: Optional[dict] = None
) -> database.Message:
    """Create new message in conversation"""
    db_message = database.Message(
        conversation_id=conversation_id,
        query_id=query_id,
        role=role,
        content=content,
        message_metadata=message_metadata
    )
    
    db.add(db_message)
    
    # Update conversation's updated_at
    conversation = db.query(database.Conversation).filter(
        database.Conversation.id == conversation_id
    ).first()
    if conversation:
        conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    return db_message


def get_conversation_messages(
    db: Session,
    conversation_id: int,
    user_id: int
) -> List[database.Message]:
    """Get all messages for a conversation"""
    # Verify user owns the conversation
    conversation = get_conversation_by_id(db, conversation_id, user_id)
    if not conversation:
        return []
    
    return db.query(database.Message).filter(
        database.Message.conversation_id == conversation_id
    ).order_by(database.Message.created_at.asc()).all()

