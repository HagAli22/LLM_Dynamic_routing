import { useState, useEffect } from 'react';
import { queriesAPI, promptsAPI, statsAPI } from '../services/api';
import { Send, Loader2, TrendingUp, Clock, DollarSign, Activity, Zap } from 'lucide-react';

export default function DashboardPage({ user }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [classification, setClassification] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await statsAPI.getUserStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleClassify = async () => {
    if (!query.trim()) return;
    
    try {
      const response = await promptsAPI.classify(query);
      setClassification(response.data);
    } catch (error) {
      console.error('Failed to classify:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await queriesAPI.processQuery({ query, skip_cache: false });
      setResult(response.data);
      loadStats(); // Refresh stats
    } catch (error) {
      setResult({
        success: false,
        error_message: error.response?.data?.detail || 'An error occurred during processing',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white shadow-2xl">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-blue-100">Process a single query with full details</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Activity className="h-8 w-8 text-blue-500" />
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Queries</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.total_queries}</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Clock className="h-8 w-8 text-green-500" />
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Average Time</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.average_processing_time.toFixed(2)}s</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Zap className="h-8 w-8 text-yellow-500" />
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Cache Hit Rate</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{(stats.cache_hit_rate * 100).toFixed(1)}%</p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="h-8 w-8 text-purple-500" />
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Cost</span>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">${stats.total_cost.toFixed(4)}</p>
          </div>
        </div>
      )}

      {/* Query Input */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Enter your query</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Write your query here..."
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClassify}
              disabled={!query.trim()}
              className="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
            >
              <TrendingUp className="inline h-5 w-5 ml-2" />
              Classify Only
            </button>
            
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg font-medium"
            >
              {loading ? (
                <>
                  <Loader2 className="inline animate-spin h-5 w-5 ml-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="inline h-5 w-5 ml-2" />
                  Send Query
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Classification Preview */}
      {classification && (
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-2xl p-6 shadow-lg border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">📊 Classification Preview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Classification</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{classification.classification}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Recommended Tier</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{classification.recommended_tier}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Expected Cost</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">${classification.estimated_cost}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Expected Time</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{classification.estimated_time}s</p>
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">📝 Result</h3>
          
          {result.success ? (
            <div className="space-y-6">
              {/* Response Text */}
              <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-xl">
                <p className="text-gray-900 dark:text-white whitespace-pre-wrap leading-relaxed">
                  {result.response}
                </p>
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Classification</p>
                  <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{result.classification}</p>
                </div>
                
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Tier</p>
                  <p className="text-lg font-bold text-purple-600 dark:text-purple-400">{result.model_tier}</p>
                </div>
                
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Model</p>
                  <p className="text-lg font-bold text-green-600 dark:text-green-400 truncate">{result.used_model}</p>
                </div>
                
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Processing Time</p>
                  <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{result.processing_time.toFixed(2)}s</p>
                </div>
                
                <div className="p-4 bg-pink-50 dark:bg-pink-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Cost</p>
                  <p className="text-lg font-bold text-pink-600 dark:text-pink-400">${result.estimated_cost.toFixed(4)}</p>
                </div>
                
                <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Cache</p>
                  <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                    {result.cache_hit ? '✅ Hit' : '❌ Miss'}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <p className="text-red-800 dark:text-red-200">{result.error_message}</p>
            </div>
          )}
        </div>
      )}

      {/* Stats Distribution */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Distribution by Tier</h3>
            <div className="space-y-3">
              {Object.entries(stats.queries_by_tier).map(([tier, count]) => (
                <div key={tier}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600 dark:text-gray-400">{tier}</span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        tier === 'tier1' ? 'bg-green-500' : tier === 'tier2' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${stats.total_queries > 0 ? (count / stats.total_queries) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Distribution by Classification</h3>
            <div className="space-y-3">
              {Object.entries(stats.queries_by_classification).map(([cls, count]) => (
                <div key={cls}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {cls === 'S' ? 'Simple' : cls === 'M' ? 'Medium' : 'Advanced'}
                    </span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        cls === 'S' ? 'bg-blue-500' : cls === 'M' ? 'bg-purple-500' : 'bg-pink-500'
                      }`}
                      style={{ width: `${stats.total_queries > 0 ? (count / stats.total_queries) * 100 : 0}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
