import { useState, useEffect } from 'react';
import { apiKeysAPI, statsAPI } from '../services/api';
import { Key, Plus, Trash2, Eye, EyeOff, BarChart2 } from 'lucide-react';

export default function SettingsPage({ user }) {
  const [apiKeys, setApiKeys] = useState([]);
  const [stats, setStats] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newKey, setNewKey] = useState({ provider: '', api_key: '', key_name: '', model_name: '', model_path: '', tier: 'tier1' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [keysRes, statsRes] = await Promise.all([
        apiKeysAPI.getAll(),
        statsAPI.getUserStats()
      ]);
      setApiKeys(keysRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleAddKey = async (e) => {
    e.preventDefault();
    try {
      await apiKeysAPI.create(newKey);
      setShowAddModal(false);
      setNewKey({ provider: '', api_key: '', key_name: '', model_name: '', model_path: '', tier: 'tier1' });
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'فشل في إضافة المفتاح');
    }
  };

  const handleDeleteKey = async (keyId) => {
    if (!confirm('هل أنت متأكد من حذف هذا المفتاح؟')) return;
    try {
      await apiKeysAPI.delete(keyId);
      loadData();
    } catch (error) {
      alert('فشل في حذف المفتاح');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6" dir="rtl">
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-2xl p-8 text-white shadow-2xl">
        <h1 className="text-3xl font-bold mb-2">الإعدادات</h1>
        <p className="text-indigo-100">إدارة حسابك و API Keys</p>
      </div>

      {/* User Info */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
        <h2 className="text-xl font-bold mb-6 text-gray-900 dark:text-white">معلومات الحساب</h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">اسم المستخدم</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{user.username}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">البريد الإلكتروني</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{user.email}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">الدور</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">{user.role}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">نوع API Keys</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {user.api_key_source === 'system_provided' ? 'النظام' : 'المستخدم'}
            </p>
          </div>
        </div>
      </div>

      {/* API Keys Management */}
      {user.api_key_source === 'user_provided' && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">API Keys</h2>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-5 w-5" /> إضافة مفتاح
            </button>
          </div>

          <div className="space-y-3">
            {apiKeys.map((key) => (
              <div key={key.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <p className="font-semibold text-gray-900 dark:text-white">{key.provider}</p>
                    {key.model_name && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                        {key.model_name}
                      </span>
                    )}
                    <span className={`text-xs px-2 py-1 rounded ${
                      key.tier === 'tier1' ? 'bg-green-100 text-green-700' :
                      key.tier === 'tier2' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {key.tier}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{key.key_name || 'بدون اسم'}</p>
                </div>
                <button
                  onClick={() => handleDeleteKey(key.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <Trash2 className="h-5 w-5" />
                </button>
              </div>
            ))}
            {apiKeys.length === 0 && (
              <p className="text-center text-gray-500 py-8">لا توجد مفاتيح API</p>
            )}
          </div>
        </div>
      )}

      {/* Statistics */}
      {stats && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
          <h2 className="text-xl font-bold mb-6 text-gray-900 dark:text-white flex items-center">
            <BarChart2 className="h-6 w-6 ml-2 text-blue-600" />
            إحصائيات الاستخدام
          </h2>
          <div className="grid grid-cols-3 gap-6">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">إجمالي الاستعلامات</p>
              <p className="text-2xl font-bold text-blue-600">{stats.total_queries}</p>
            </div>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">متوسط الوقت</p>
              <p className="text-2xl font-bold text-green-600">{stats.average_processing_time.toFixed(2)}s</p>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Cache Hit Rate</p>
              <p className="text-2xl font-bold text-purple-600">{(stats.cache_hit_rate * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Add Key Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAddModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-6">إضافة API Key</h3>
            <form onSubmit={handleAddKey} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">المزود</label>
                <input
                  type="text"
                  required
                  value={newKey.provider}
                  onChange={(e) => setNewKey({ ...newKey, provider: e.target.value })}
                  placeholder="مثل: openai, anthropic"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="password"
                  required
                  value={newKey.api_key}
                  onChange={(e) => setNewKey({ ...newKey, api_key: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">اسم المفتاح (اختياري)</label>
                <input
                  type="text"
                  value={newKey.key_name}
                  onChange={(e) => setNewKey({ ...newKey, key_name: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">اسم الموديل (اختياري)</label>
                <input
                  type="text"
                  value={newKey.model_name}
                  onChange={(e) => setNewKey({ ...newKey, model_name: e.target.value })}
                  placeholder="مثل: qwen-2.5-72b-instruct"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                />
                <p className="text-xs text-gray-500 mt-1">للعرض فقط</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">مسار الموديل (اختياري)</label>
                <input
                  type="text"
                  value={newKey.model_path}
                  onChange={(e) => setNewKey({ ...newKey, model_path: e.target.value })}
                  placeholder="مثل: qwen/qwen-2.5-72b-instruct:free"
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                />
                <p className="text-xs text-gray-500 mt-1">المسار الكامل للموديل. إذا تركته فارغاً، سيستخدم النظام الموديلات الافتراضية</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Tier</label>
                <select
                  value={newKey.tier}
                  onChange={(e) => setNewKey({ ...newKey, tier: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700"
                >
                  <option value="tier1">Tier 1 - أسرع وأرخص</option>
                  <option value="tier2">Tier 2 - متوسط</option>
                  <option value="tier3">Tier 3 - أقوى وأغلى</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">موديلك سيكون الأول في هذا الـ tier</p>
              </div>
              <div className="flex gap-3">
                <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg">
                  إضافة
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg"
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
