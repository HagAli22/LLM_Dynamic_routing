# 🚀 البدء السريع - نظام التقييم

## خطوات التشغيل

### 1. تشغيل Migration
```bash
python migrate_rating_system.py
```

### 2. اختبار النظام
```bash
python test_rating_system.py
```

### 3. تشغيل API Server
```bash
python production_api.py
```

## 📱 استخدام API

### إضافة تقييم
```bash
curl -X POST http://localhost:8000/api/rating/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": 1,
    "model_identifier": "qwen/qwen-2.5-72b-instruct:free",
    "feedback_type": "like",
    "comment": "Great!"
  }'
```

### عرض لوحة المتصدرين
```bash
curl http://localhost:8000/api/rating/leaderboard/tier1?limit=5
```

### إحصائيات موديل
```bash
curl http://localhost:8000/api/rating/models/qwen%2Fqwen-2.5-72b-instruct%3Afree/stats
```

## 🎯 أمثلة سريعة

### Python
```python
from database import SessionLocal
from model_rating_system import ModelRatingManager

db = SessionLocal()
manager = ModelRatingManager(db)

# إضافة إعجاب
manager.add_feedback(
    query_id=1,
    user_id=1,
    model_identifier="qwen/qwen-2.5-72b-instruct:free",
    feedback_type='like'
)

# عرض الترتيب
ranked = manager.get_ranked_models('tier1')
print(f"Top model: {ranked[0]}")
```

### JavaScript (Frontend)
```javascript
// إضافة تقييم
const response = await axios.post('/api/rating/feedback', {
  query_id: queryId,
  model_identifier: modelId,
  feedback_type: 'like'
}, {
  headers: { Authorization: `Bearer ${token}` }
});

console.log(`New score: ${response.data.new_score}`);
```

## 📊 نظام النقاط

| التقييم | النقاط | الأيقونة |
|---------|--------|----------|
| إعجاب   | +5     | 👍       |
| عدم إعجاب | -5   | 👎       |
| نجمة    | +10    | ⭐       |

## 🔧 استكشاف الأخطاء

### خطأ: جداول غير موجودة
```bash
python migrate_rating_system.py
```

### خطأ: موديلات غير مرتبة
```python
router.refresh_model_rankings()
```

## 📝 ملاحظات مهمة

1. كل موديل يبدأ بـ **100 نقطة**
2. الترتيب يتحدث **تلقائياً** مع كل تقييم
3. الموديل الأعلى نقاطاً يُجرب **أولاً**
4. يمكن للمستخدم تقييم نفس الموديل **عدة مرات**

## 🎨 Frontend Components

### استخدام ModelRating Component
```jsx
import ModelRating from './components/ModelRating';

<ModelRating
  queryId={123}
  modelIdentifier="qwen/qwen-2.5-72b-instruct:free"
  modelName="Qwen 2.5 72B"
  onRatingSuccess={(data) => {
    console.log('Rating added!', data);
  }}
/>
```

### إضافة صفحة Leaderboard للـ Router
```jsx
// في App.jsx
import LeaderboardPage from './pages/LeaderboardPage';

<Route path="/leaderboard" element={<LeaderboardPage />} />
```

## 🔗 روابط مفيدة

- [README الكامل](./RATING_SYSTEM_README.md)
- [API Documentation](http://localhost:8000/docs)
- [Database Schema](./database.py)
