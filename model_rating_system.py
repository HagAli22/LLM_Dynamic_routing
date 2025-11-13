"""
Model Rating System - نظام تقييم الموديلات الديناميكي
يتيح للمستخدمين تقييم الموديلات وإعادة ترتيبها تلقائياً
"""

from sqlalchemy.orm import Session
from database import ModelRating, ModelFeedback, QueryLog
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ModelRatingManager:
    """إدارة نظام تقييم الموديلات"""
    
    # نقاط التقييم
    POINTS = {
        'like': 5,
        'dislike': -5,
        'star': 10
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_feedback(
        self, 
        query_id: int,
        user_id: int,
        model_identifier: str,
        feedback_type: str,
        comment: Optional[str] = None
    ) -> Dict:
        """
        إضافة تقييم جديد للموديل
        
        Args:
            query_id: معرف الاستعلام
            user_id: معرف المستخدم
            model_identifier: معرف الموديل
            feedback_type: نوع التقييم (like/dislike/star)
            comment: تعليق اختياري
        
        Returns:
            Dict with updated model info
        """
        try:
            # التحقق من صحة نوع التقييم
            if feedback_type not in self.POINTS:
                raise ValueError(f"Invalid feedback type: {feedback_type}")
            
            points_change = self.POINTS[feedback_type]
            
            # إضافة التقييم الفردي
            feedback = ModelFeedback(
                query_id=query_id,
                user_id=user_id,
                model_identifier=model_identifier,
                feedback_type=feedback_type,
                points_change=points_change,
                comment=comment
            )
            self.db.add(feedback)
            
            # تحديث نقاط الموديل
            model_rating = self.db.query(ModelRating).filter(
                ModelRating.model_identifier == model_identifier
            ).first()
            
            if not model_rating:
                # إنشاء سجل جديد إذا لم يكن موجود
                # محاولة تحديد الـ tier من config
                from config import MODELS_CONFIG
                detected_tier = "tier1"
                for tier, models in MODELS_CONFIG.items():
                    for model in models:
                        if isinstance(model, (list, tuple)) and len(model) >= 2:
                            if model[1] == model_identifier:
                                detected_tier = tier
                                break
                        elif model == model_identifier:
                            detected_tier = tier
                            break
                
                model_rating = ModelRating(
                    model_identifier=model_identifier,
                    model_name=model_identifier.split('/')[-1].replace(':free', ''),
                    tier=detected_tier,
                    score=100
                )
                self.db.add(model_rating)
                logger.info(f"✨ Created new model rating: {model_identifier} in {detected_tier}")
            
            # تحديث النقاط والإحصائيات
            model_rating.score += points_change
            model_rating.total_feedbacks += 1
            
            if feedback_type == 'like':
                model_rating.total_likes += 1
            elif feedback_type == 'dislike':
                model_rating.total_dislikes += 1
            elif feedback_type == 'star':
                model_rating.total_stars += 1
            
            model_rating.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Feedback added: {feedback_type} for {model_identifier}, new score: {model_rating.score}")
            
            return {
                'success': True,
                'model_identifier': model_identifier,
                'feedback_type': feedback_type,
                'points_change': points_change,
                'new_score': model_rating.score,
                'total_feedbacks': model_rating.total_feedbacks
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error adding feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ranked_models(self, tier: str) -> List[str]:
        """
        الحصول على الموديلات مرتبة حسب النقاط في tier معين
        
        Args:
            tier: اسم الـ tier (tier1, tier2, tier3)
        
        Returns:
            قائمة بمعرفات الموديلات مرتبة من الأعلى للأقل
        """
        try:
            models = self.db.query(ModelRating).filter(
                ModelRating.tier == tier
            ).order_by(ModelRating.score.desc()).all()
            
            return [model.model_identifier for model in models]
            
        except Exception as e:
            logger.error(f"❌ Error getting ranked models: {e}")
            return []
    
    def get_all_ranked_models(self) -> Dict[str, List[str]]:
        """
        الحصول على جميع الموديلات مرتبة حسب النقاط لكل tier
        
        Returns:
            Dict with tier names as keys and ranked model lists as values
        """
        return {
            'tier1': self.get_ranked_models('tier1'),
            'tier2': self.get_ranked_models('tier2'),
            'tier3': self.get_ranked_models('tier3')
        }
    
    def get_model_stats(self, model_identifier: str) -> Optional[Dict]:
        """
        الحصول على إحصائيات موديل معين
        
        Args:
            model_identifier: معرف الموديل
        
        Returns:
            Dict with model statistics
        """
        try:
            model = self.db.query(ModelRating).filter(
                ModelRating.model_identifier == model_identifier
            ).first()
            
            if not model:
                return None
            
            return {
                'model_identifier': model.model_identifier,
                'model_name': model.model_name,
                'tier': model.tier,
                'score': model.score,
                'total_likes': model.total_likes,
                'total_dislikes': model.total_dislikes,
                'total_stars': model.total_stars,
                'total_feedbacks': model.total_feedbacks,
                'total_uses': model.total_uses,
                'successful_uses': model.successful_uses,
                'failed_uses': model.failed_uses,
                'success_rate': (model.successful_uses / model.total_uses * 100) if model.total_uses > 0 else 0,
                'avg_response_time': model.avg_response_time,
                'avg_cost': model.avg_cost,
                'last_used': model.last_used.isoformat() if model.last_used else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting model stats: {e}")
            return None
    
    def get_tier_leaderboard(self, tier: str, limit: int = 10) -> List[Dict]:
        """
        الحصول على لوحة المتصدرين لـ tier معين
        
        Args:
            tier: اسم الـ tier
            limit: عدد الموديلات المطلوبة
        
        Returns:
            قائمة بالموديلات مع إحصائياتها
        """
        try:
            models = self.db.query(ModelRating).filter(
                ModelRating.tier == tier
            ).order_by(ModelRating.score.desc()).limit(limit).all()
            
            leaderboard = []
            for rank, model in enumerate(models, 1):
                leaderboard.append({
                    'rank': rank,
                    'model_identifier': model.model_identifier,
                    'model_name': model.model_name,
                    'score': model.score,
                    'total_likes': model.total_likes,
                    'total_dislikes': model.total_dislikes,
                    'total_stars': model.total_stars,
                    'total_feedbacks': model.total_feedbacks,
                    'success_rate': (model.successful_uses / model.total_uses * 100) if model.total_uses > 0 else 0
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            return []
    
    def update_model_usage(
        self,
        model_identifier: str,
        success: bool,
        response_time: float,
        cost: float
    ):
        """
        تحديث إحصائيات استخدام الموديل
        
        Args:
            model_identifier: معرف الموديل
            success: هل نجح الاستعلام
            response_time: وقت الاستجابة
            cost: التكلفة
        """
        try:
            model = self.db.query(ModelRating).filter(
                ModelRating.model_identifier == model_identifier
            ).first()
            
            if not model:
                return
            
            model.total_uses += 1
            if success:
                model.successful_uses += 1
            else:
                model.failed_uses += 1
            
            # تحديث المتوسطات
            if model.total_uses > 1:
                model.avg_response_time = (
                    (model.avg_response_time * (model.total_uses - 1) + response_time) / model.total_uses
                )
                model.avg_cost = (
                    (model.avg_cost * (model.total_uses - 1) + cost) / model.total_uses
                )
            else:
                model.avg_response_time = response_time
                model.avg_cost = cost
            
            model.last_used = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error updating model usage: {e}")
            self.db.rollback()
    
    def reset_model_score(self, model_identifier: str, new_score: int = 100):
        """
        إعادة تعيين نقاط موديل معين
        
        Args:
            model_identifier: معرف الموديل
            new_score: النقاط الجديدة (افتراضي 100)
        """
        try:
            model = self.db.query(ModelRating).filter(
                ModelRating.model_identifier == model_identifier
            ).first()
            
            if model:
                model.score = new_score
                model.updated_at = datetime.utcnow()
                self.db.commit()
                logger.info(f"✅ Reset score for {model_identifier} to {new_score}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error resetting model score: {e}")
            self.db.rollback()
            return False
    
    def get_feedback_history(
        self,
        model_identifier: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        الحصول على سجل التقييمات
        
        Args:
            model_identifier: تصفية حسب الموديل (اختياري)
            user_id: تصفية حسب المستخدم (اختياري)
            limit: عدد السجلات
        
        Returns:
            قائمة بالتقييمات
        """
        try:
            query = self.db.query(ModelFeedback)
            
            if model_identifier:
                query = query.filter(ModelFeedback.model_identifier == model_identifier)
            
            if user_id:
                query = query.filter(ModelFeedback.user_id == user_id)
            
            feedbacks = query.order_by(ModelFeedback.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': fb.id,
                    'query_id': fb.query_id,
                    'user_id': fb.user_id,
                    'model_identifier': fb.model_identifier,
                    'feedback_type': fb.feedback_type,
                    'points_change': fb.points_change,
                    'comment': fb.comment,
                    'created_at': fb.created_at.isoformat()
                }
                for fb in feedbacks
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting feedback history: {e}")
            return []
