# نظام تقييم الموديلات الديناميكي
# Dynamic Model Rating System

## 📋 نظرة عامة

نظام تقييم ذكي يسمح للمستخدمين بتقييم أداء الموديلات المختلفة، مما يؤدي إلى إعادة ترتيب تلقائي للموديلات حسب النقاط.

## ⭐ المميزات

### نظام النقاط
- 👍 **إعجاب (Like)**: +5 نقاط
- 👎 **عدم إعجاب (Dislike)**: -5 نقاط
- ⭐ **نجمة (Star)**: +10 نقاط

### الترتيب التلقائي
- كل موديل يبدأ بـ 100 نقطة
- مع كل تقييم، تتحدث النقاط تلقائياً
- الموديلات تُرتب من الأعلى للأقل في كل tier
- الموديل صاحب أعلى نقاط يُجرب أولاً

### الإحصائيات
- عدد الاستخدامات الكلي
- معدل النجاح
- متوسط وقت الاستجابة
- متوسط التكلفة
- سجل كامل للتقييمات

## 🚀 التثبيت والإعداد

### 1. تشغيل Migration
```bash
python migrate_rating_system.py
```

هذا السكريبت سيقوم بـ:
- إنشاء جداول `model_ratings` و `model_feedbacks`
- تهيئة جميع الموديلات من `config.py` بنقاط ابتدائية (100)

### 2. اختبار النظام
```bash
python test_rating_system.py
```

## 📡 API Endpoints

### إضافة تقييم
```http
POST /api/rating/feedback
Authorization: Bearer {token}

{
  "query_id": 123,
  "model_identifier": "qwen/qwen-2.5-72b-instruct:free",
  "feedback_type": "like",  // like, dislike, or star
  "comment": "Great response!"
}
```

**Response:**
```json
{
  "success": true,
  "model_identifier": "qwen/qwen-2.5-72b-instruct:free",
  "feedback_type": "like",
  "points_change": 5,
  "new_score": 105,
  "total_feedbacks": 1
}
```

### الحصول على إحصائيات موديل
```http
GET /api/rating/models/{model_identifier}/stats
```

**Response:**
```json
{
  "model_identifier": "qwen/qwen-2.5-72b-instruct:free",
  "model_name": "qwen-2.5-72b-instruct",
  "tier": "tier1",
  "score": 105,
  "total_likes": 1,
  "total_dislikes": 0,
  "total_stars": 0,
  "total_feedbacks": 1,
  "total_uses": 10,
  "successful_uses": 9,
  "failed_uses": 1,
  "success_rate": 90.0,
  "avg_response_time": 2.5,
  "avg_cost": 0.001
}
```

### لوحة المتصدرين
```http
GET /api/rating/leaderboard/{tier}?limit=10
```

**Response:**
```json
[
  {
    "rank": 1,
    "model_identifier": "qwen/qwen-2.5-72b-instruct:free",
    "model_name": "qwen-2.5-72b-instruct",
    "score": 115,
    "total_likes": 3,
    "total_dislikes": 0,
    "total_stars": 1,
    "total_feedbacks": 4,
    "success_rate": 95.0
  }
]
```

### جميع الموديلات المرتبة
```http
GET /api/rating/ranked-models
```

**Response:**
```json
{
  "tier1": ["model1", "model2", "model3"],
  "tier2": ["model4", "model5"],
  "tier3": ["model6", "model7"]
}
```

### سجل التقييمات
```http
GET /api/rating/feedback-history?model_identifier={model}&limit=50
Authorization: Bearer {token}
```

### إعادة تعيين النقاط (Admin فقط)
```http
POST /api/rating/models/{model_identifier}/reset-score?new_score=100
Authorization: Bearer {admin_token}
```

### ملخص الإحصائيات
```http
GET /api/rating/stats/summary
```

## 🔧 الاستخدام في الكود

### إضافة تقييم
```python
from database import SessionLocal
from model_rating_system import ModelRatingManager

db = SessionLocal()
rating_manager = ModelRatingManager(db)

# إضافة إعجاب
result = rating_manager.add_feedback(
    query_id=123,
    user_id=1,
    model_identifier="qwen/qwen-2.5-72b-instruct:free",
    feedback_type='like',
    comment='Excellent response!'
)

print(f"New score: {result['new_score']}")
```

### الحصول على الموديلات المرتبة
```python
# موديلات tier1 مرتبة حسب النقاط
ranked_models = rating_manager.get_ranked_models('tier1')
print(f"Top model: {ranked_models[0]}")

# جميع الـ tiers
all_ranked = rating_manager.get_all_ranked_models()
```

### إحصائيات موديل
```python
stats = rating_manager.get_model_stats("qwen/qwen-2.5-72b-instruct:free")
print(f"Score: {stats['score']}")
print(f"Success rate: {stats['success_rate']}%")
```

### لوحة المتصدرين
```python
leaderboard = rating_manager.get_tier_leaderboard('tier1', limit=10)
for item in leaderboard:
    print(f"#{item['rank']} {item['model_name']} - Score: {item['score']}")
```

## 🔄 التكامل مع Router

الـ Router يتم تحديثه تلقائياً ليستخدم الترتيب الجديد:

```python
from langgraph_router import Router
from database import SessionLocal

db = SessionLocal()

router = Router(
    models_config=MODELS_CONFIG,
    cache=cache,
    classifier=classifier,
    llm_client=llm_client,
    db_session=db  # إضافة database session
)

# الموديلات الآن مرتبة حسب النقاط تلقائياً
result = router.route("What is Python?")
```

### تحديث الترتيب يدوياً
```python
# تحديث الترتيب بعد إضافة تقييمات جديدة
router.refresh_model_rankings()
```

## 📊 جداول قاعدة البيانات

### model_ratings
```sql
- id: معرف فريد
- model_identifier: معرف الموديل الكامل
- model_name: اسم الموديل للعرض
- tier: tier1, tier2, tier3
- score: النقاط الحالية
- total_likes: عدد الإعجابات
- total_dislikes: عدد عدم الإعجاب
- total_stars: عدد النجوم
- total_feedbacks: إجمالي التقييمات
- total_uses: عدد الاستخدامات
- successful_uses: الاستخدامات الناجحة
- failed_uses: الاستخدامات الفاشلة
- avg_response_time: متوسط وقت الاستجابة
- avg_cost: متوسط التكلفة
- created_at, updated_at, last_used
```

### model_feedbacks
```sql
- id: معرف فريد
- query_id: معرف الاستعلام
- user_id: معرف المستخدم
- model_identifier: معرف الموديل
- feedback_type: like, dislike, star
- points_change: التغيير في النقاط (+5, -5, +10)
- comment: تعليق اختياري
- created_at: وقت الإنشاء
```

## 🎯 أمثلة الاستخدام

### مثال 1: إضافة تقييمات متعددة
```python
models_to_rate = [
    ("model1", "like", "Fast and accurate"),
    ("model2", "star", "Excellent quality"),
    ("model3", "dislike", "Slow response")
]

for model, feedback_type, comment in models_to_rate:
    rating_manager.add_feedback(
        query_id=query_id,
        user_id=user_id,
        model_identifier=model,
        feedback_type=feedback_type,
        comment=comment
    )
```

### مثال 2: عرض أفضل 3 موديلات
```python
for tier in ['tier1', 'tier2', 'tier3']:
    print(f"\n{tier.upper()} Top 3:")
    leaderboard = rating_manager.get_tier_leaderboard(tier, limit=3)
    for item in leaderboard:
        print(f"  {item['rank']}. {item['model_name']} - {item['score']} pts")
```

### مثال 3: تحليل الأداء
```python
stats = rating_manager.get_model_stats(model_identifier)
if stats:
    print(f"Model: {stats['model_name']}")
    print(f"Score: {stats['score']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
    print(f"Avg Response Time: {stats['avg_response_time']:.2f}s")
    print(f"Avg Cost: ${stats['avg_cost']:.4f}")
```

## 🔐 الصلاحيات

- **المستخدمون العاديون**: يمكنهم إضافة تقييمات ورؤية إحصائياتهم
- **الأدمن**: يمكنهم رؤية جميع التقييمات وإعادة تعيين النقاط

## 📝 ملاحظات

1. النقاط الابتدائية لكل موديل: 100
2. لا يوجد حد أدنى أو أقصى للنقاط
3. الترتيب يتم تلقائياً عند كل استعلام
4. يمكن للمستخدم تقييم نفس الموديل عدة مرات
5. التقييمات مرتبطة بـ query_id محدد

## 🐛 استكشاف الأخطاء

### المشكلة: الجداول غير موجودة
```bash
python migrate_rating_system.py
```

### المشكلة: الموديلات غير مرتبة
```python
router.refresh_model_rankings()
```

### المشكلة: نقاط غير صحيحة
```python
# إعادة تعيين نقاط موديل معين
rating_manager.reset_model_score(model_identifier, 100)
```

## 📞 الدعم

للمزيد من المعلومات أو الإبلاغ عن مشاكل، يرجى فتح issue في المشروع.
