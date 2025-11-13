"""
Rating API Endpoints - نقاط نهاية API للتقييمات
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from database import get_db
from model_rating_system import ModelRatingManager
from auth import get_current_user
from database import User

router = APIRouter(prefix="/rating", tags=["Model Rating"])


# ==================== REQUEST/RESPONSE MODELS ====================

class FeedbackRequest(BaseModel):
    """طلب إضافة تقييم"""
    query_id: int = Field(..., description="معرف الاستعلام")
    model_identifier: str = Field(..., description="معرف الموديل")
    feedback_type: str = Field(..., description="نوع التقييم: like, dislike, star")
    comment: Optional[str] = Field(None, description="تعليق اختياري")


class FeedbackResponse(BaseModel):
    """استجابة التقييم"""
    success: bool
    model_identifier: str
    feedback_type: str
    points_change: int
    new_score: int
    total_feedbacks: int


class ModelStatsResponse(BaseModel):
    """إحصائيات الموديل"""
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
    last_used: Optional[str]


class LeaderboardItem(BaseModel):
    """عنصر في لوحة المتصدرين"""
    rank: int
    model_identifier: str
    model_name: str
    score: int
    total_likes: int
    total_dislikes: int
    total_stars: int
    total_feedbacks: int
    success_rate: float


# ==================== ENDPOINTS ====================

@router.post("/feedback", response_model=FeedbackResponse)
async def add_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إضافة تقييم لموديل معين
    
    - **query_id**: معرف الاستعلام
    - **model_identifier**: معرف الموديل
    - **feedback_type**: like (👍 +5), dislike (👎 -5), star (⭐ +10)
    - **comment**: تعليق اختياري
    """
    rating_manager = ModelRatingManager(db)
    
    result = rating_manager.add_feedback(
        query_id=feedback.query_id,
        user_id=current_user.id,
        model_identifier=feedback.model_identifier,
        feedback_type=feedback.feedback_type,
        comment=feedback.comment
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add feedback'))
    
    return FeedbackResponse(**result)


@router.get("/models/{model_identifier}/stats", response_model=ModelStatsResponse)
async def get_model_stats(
    model_identifier: str,
    db: Session = Depends(get_db)
):
    """
    الحصول على إحصائيات موديل معين
    """
    rating_manager = ModelRatingManager(db)
    stats = rating_manager.get_model_stats(model_identifier)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelStatsResponse(**stats)


@router.get("/leaderboard/{tier}", response_model=List[LeaderboardItem])
async def get_leaderboard(
    tier: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    الحصول على لوحة المتصدرين لـ tier معين
    
    - **tier**: tier1, tier2, أو tier3
    - **limit**: عدد الموديلات (افتراضي 10)
    """
    if tier not in ['tier1', 'tier2', 'tier3']:
        raise HTTPException(status_code=400, detail="Invalid tier. Must be tier1, tier2, or tier3")
    
    rating_manager = ModelRatingManager(db)
    leaderboard = rating_manager.get_tier_leaderboard(tier, limit)
    
    return [LeaderboardItem(**item) for item in leaderboard]


@router.get("/leaderboard", response_model=dict)
async def get_all_leaderboards(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    الحصول على لوحة المتصدرين لجميع الـ tiers
    """
    rating_manager = ModelRatingManager(db)
    
    return {
        'tier1': rating_manager.get_tier_leaderboard('tier1', limit),
        'tier2': rating_manager.get_tier_leaderboard('tier2', limit),
        'tier3': rating_manager.get_tier_leaderboard('tier3', limit)
    }


@router.get("/ranked-models")
async def get_ranked_models(
    db: Session = Depends(get_db)
):
    """
    الحصول على جميع الموديلات مرتبة حسب النقاط
    """
    rating_manager = ModelRatingManager(db)
    return rating_manager.get_all_ranked_models()


@router.get("/feedback-history")
async def get_feedback_history(
    model_identifier: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على سجل التقييمات
    
    - **model_identifier**: تصفية حسب الموديل (اختياري)
    - **limit**: عدد السجلات (افتراضي 50)
    """
    rating_manager = ModelRatingManager(db)
    
    # المستخدمون العاديون يرون تقييماتهم فقط
    # الأدمن يرى كل التقييمات
    user_id = None if current_user.role.value == "admin" else current_user.id
    
    history = rating_manager.get_feedback_history(
        model_identifier=model_identifier,
        user_id=user_id,
        limit=limit
    )
    
    return {
        'total': len(history),
        'feedbacks': history
    }


@router.post("/models/{model_identifier}/reset-score")
async def reset_model_score(
    model_identifier: str,
    new_score: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إعادة تعيين نقاط موديل معين (للأدمن فقط)
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rating_manager = ModelRatingManager(db)
    success = rating_manager.reset_model_score(model_identifier, new_score)
    
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        'success': True,
        'message': f'Score reset to {new_score} for {model_identifier}'
    }


@router.get("/stats/summary")
async def get_rating_summary(
    db: Session = Depends(get_db)
):
    """
    ملخص إحصائيات نظام التقييم
    """
    from database import ModelRating, ModelFeedback
    
    total_models = db.query(ModelRating).count()
    total_feedbacks = db.query(ModelFeedback).count()
    
    # أعلى موديل في كل tier
    top_models = {}
    for tier in ['tier1', 'tier2', 'tier3']:
        top_model = db.query(ModelRating).filter(
            ModelRating.tier == tier
        ).order_by(ModelRating.score.desc()).first()
        
        if top_model:
            top_models[tier] = {
                'model_identifier': top_model.model_identifier,
                'model_name': top_model.model_name,
                'score': top_model.score
            }
    
    # إحصائيات التقييمات
    total_likes = db.query(ModelFeedback).filter(ModelFeedback.feedback_type == 'like').count()
    total_dislikes = db.query(ModelFeedback).filter(ModelFeedback.feedback_type == 'dislike').count()
    total_stars = db.query(ModelFeedback).filter(ModelFeedback.feedback_type == 'star').count()
    
    return {
        'total_models': total_models,
        'total_feedbacks': total_feedbacks,
        'total_likes': total_likes,
        'total_dislikes': total_dislikes,
        'total_stars': total_stars,
        'top_models': top_models
    }


@router.post("/refresh-rankings")
async def refresh_model_rankings(
    db: Session = Depends(get_db)
):
    """
    تحديث ترتيب الموديلات يدوياً
    يستخدم لإعادة تحميل الترتيب بعد التقييمات
    """
    try:
        rating_manager = ModelRatingManager(db)
        ranked_models = rating_manager.get_all_ranked_models()
        
        return {
            'success': True,
            'message': 'Model rankings refreshed successfully',
            'ranked_models': ranked_models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
