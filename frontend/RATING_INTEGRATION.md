# دمج نظام التقييم في Frontend

## 📦 المكونات الجاهزة

### 1. ModelRating Component
مكون لإضافة أزرار التقييم (Like, Dislike, Star)

**الموقع:** `src/components/ModelRating.jsx`

**الاستخدام:**
```jsx
import ModelRating from '../components/ModelRating';

<ModelRating
  queryId={response.id}
  modelIdentifier={response.used_model}
  modelName={response.model_name}
  onRatingSuccess={(data) => {
    console.log('Rating submitted:', data);
    // تحديث UI أو عرض رسالة نجاح
  }}
/>
```

### 2. LeaderboardPage
صفحة كاملة لعرض لوحة المتصدرين

**الموقع:** `src/pages/LeaderboardPage.jsx`

**إضافتها للـ Router:**
```jsx
// في App.jsx
import LeaderboardPage from './pages/LeaderboardPage';

<Route path="/leaderboard" element={<LeaderboardPage />} />
```

## 🔧 التكامل مع الصفحات الموجودة

### ChatbotPage
أضف مكون التقييم بعد كل رد من الـ assistant:

```jsx
// في ChatbotPage.jsx
import ModelRating from '../components/ModelRating';

// داخل render الرسائل
{message.role === 'assistant' && message.metadata && (
  <ModelRating
    queryId={message.metadata.query_id}
    modelIdentifier={message.metadata.used_model}
    modelName={message.metadata.model_name || 'Model'}
    onRatingSuccess={(data) => {
      // يمكن تحديث الرسالة لإظهار أن التقييم تم
      console.log('Feedback submitted:', data);
    }}
  />
)}
```

### DashboardPage
أضف التقييم بعد عرض النتيجة:

```jsx
// في DashboardPage.jsx
{result && result.success && (
  <div className="mt-4">
    <ModelRating
      queryId={result.id}
      modelIdentifier={result.used_model}
      modelName={result.model_name}
    />
  </div>
)}
```

### BatchProcessingPage
أضف عمود للتقييم في جدول النتائج:

```jsx
// في BatchProcessingPage.jsx
<td>
  <ModelRating
    queryId={result.id}
    modelIdentifier={result.used_model}
    modelName={result.model_name}
  />
</td>
```

## 🎨 تخصيص التصميم

### تغيير الألوان
```jsx
// في ModelRating.jsx
const buttonStyles = {
  like: 'bg-green-100 hover:bg-green-200 text-green-600',
  dislike: 'bg-red-100 hover:bg-red-200 text-red-600',
  star: 'bg-yellow-100 hover:bg-yellow-200 text-yellow-600',
};
```

### تغيير الأيقونات
```jsx
import { Heart, X, Award } from 'lucide-react';

// استبدل ThumbsUp, ThumbsDown, Star بالأيقونات الجديدة
```

### إضافة رسوم متحركة
```jsx
// أضف Tailwind animations
className="transition-all duration-300 hover:scale-110 active:scale-95"
```

## 📊 عرض الإحصائيات

### إضافة بطاقة إحصائيات في Dashboard
```jsx
import { useEffect, useState } from 'react';
import axios from 'axios';

const ModelStats = ({ modelIdentifier }) => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axios.get(`/api/rating/models/${encodeURIComponent(modelIdentifier)}/stats`)
      .then(res => setStats(res.data))
      .catch(err => console.error(err));
  }, [modelIdentifier]);

  if (!stats) return null;

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="font-bold mb-2">{stats.model_name}</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>النقاط: {stats.score}</div>
        <div>معدل النجاح: {stats.success_rate.toFixed(1)}%</div>
        <div>👍 {stats.total_likes}</div>
        <div>👎 {stats.total_dislikes}</div>
        <div>⭐ {stats.total_stars}</div>
        <div>استخدامات: {stats.total_uses}</div>
      </div>
    </div>
  );
};
```

## 🔗 إضافة رابط Leaderboard في Navigation

### في Layout.jsx
```jsx
const menuItems = [
  { name: 'الدردشة', path: '/chatbot', icon: MessageSquare },
  { name: 'لوحة التحكم', path: '/dashboard', icon: LayoutDashboard },
  { name: 'المعالجة الجماعية', path: '/batch', icon: FileText },
  { name: 'لوحة المتصدرين', path: '/leaderboard', icon: Trophy }, // جديد
  { name: 'الإعدادات', path: '/settings', icon: Settings },
];
```

## 🎯 أمثلة متقدمة

### عرض التقييم مع Animation
```jsx
const [showRating, setShowRating] = useState(false);

useEffect(() => {
  // إظهار التقييم بعد ثانيتين من الرد
  const timer = setTimeout(() => setShowRating(true), 2000);
  return () => clearTimeout(timer);
}, []);

{showRating && (
  <div className="animate-fade-in">
    <ModelRating {...props} />
  </div>
)}
```

### تتبع التقييمات المحلية
```jsx
const [userRatings, setUserRatings] = useState({});

const handleRatingSuccess = (data) => {
  setUserRatings(prev => ({
    ...prev,
    [data.model_identifier]: data.feedback_type
  }));
  
  // حفظ في localStorage
  localStorage.setItem('userRatings', JSON.stringify(userRatings));
};
```

### عرض إحصائيات سريعة
```jsx
const QuickStats = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    axios.get('/api/rating/stats/summary')
      .then(res => setSummary(res.data));
  }, []);

  return (
    <div className="flex gap-4">
      <div className="text-center">
        <div className="text-2xl font-bold text-green-600">
          {summary?.total_likes || 0}
        </div>
        <div className="text-xs text-gray-600">إعجابات</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-yellow-600">
          {summary?.total_stars || 0}
        </div>
        <div className="text-xs text-gray-600">نجوم</div>
      </div>
    </div>
  );
};
```

## 🐛 معالجة الأخطاء

### عرض رسائل خطأ واضحة
```jsx
const [error, setError] = useState(null);

try {
  // API call
} catch (err) {
  if (err.response?.status === 401) {
    setError('يرجى تسجيل الدخول أولاً');
  } else if (err.response?.status === 400) {
    setError('تقييم غير صالح');
  } else {
    setError('حدث خطأ، يرجى المحاولة مرة أخرى');
  }
}
```

### Retry Logic
```jsx
const submitFeedback = async (feedbackType, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios.post('/api/rating/feedback', data);
      return response.data;
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

## 📱 Responsive Design

### تصميم متجاوب للموبايل
```jsx
<div className="flex flex-col sm:flex-row items-center gap-2">
  <div className="text-sm text-gray-600 mb-2 sm:mb-0">
    قيّم الإجابة:
  </div>
  <div className="flex gap-2">
    {/* أزرار التقييم */}
  </div>
</div>
```

## 🔔 Notifications

### إضافة Toast Notifications
```jsx
import { toast } from 'react-toastify';

const handleRatingSuccess = (data) => {
  const emoji = data.feedback_type === 'like' ? '👍' : 
                data.feedback_type === 'dislike' ? '👎' : '⭐';
  
  toast.success(`${emoji} شكراً! ${data.points_change > 0 ? '+' : ''}${data.points_change} نقطة`, {
    position: 'bottom-right',
    autoClose: 3000,
  });
};
```

## 🎨 Dark Mode Support

```jsx
<button
  className={`p-2 rounded-full transition-all ${
    theme === 'dark'
      ? 'bg-green-900 hover:bg-green-800'
      : 'bg-green-100 hover:bg-green-200'
  }`}
>
  <ThumbsUp className={`w-5 h-5 ${
    theme === 'dark' ? 'text-green-300' : 'text-green-600'
  }`} />
</button>
```
