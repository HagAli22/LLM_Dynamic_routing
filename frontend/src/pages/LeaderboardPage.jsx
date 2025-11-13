/**
 * Leaderboard Page
 * صفحة لوحة المتصدرين
 */

import React, { useState, useEffect } from 'react';
import { Trophy, TrendingUp, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import axios from 'axios';
import Layout from '../components/Layout';

const LeaderboardPage = () => {
  const [leaderboards, setLeaderboards] = useState({
    tier1: [],
    tier2: [],
    tier3: [],
  });
  const [selectedTier, setSelectedTier] = useState('tier1');
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchLeaderboards();
    fetchSummary();
  }, []);

  const fetchLeaderboards = async () => {
    try {
      const response = await axios.get('/api/rating/leaderboard?limit=10');
      setLeaderboards(response.data);
    } catch (error) {
      console.error('Error fetching leaderboards:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get('/api/rating/stats/summary');
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const tierNames = {
    tier1: 'المستوى الأول - Simple',
    tier2: 'المستوى الثاني - Medium',
    tier3: 'المستوى الثالث - Advanced',
  };

  const getMedalColor = (rank) => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-gray-400';
    if (rank === 3) return 'text-orange-600';
    return 'text-gray-600';
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Trophy className="w-8 h-8 text-yellow-500" />
            لوحة المتصدرين
          </h1>
          <p className="text-gray-600 mt-2">
            ترتيب الموديلات حسب تقييمات المستخدمين
          </p>
        </div>

        {/* Summary Stats */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600">إجمالي الموديلات</div>
              <div className="text-2xl font-bold text-gray-900">
                {summary.total_models}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <ThumbsUp className="w-4 h-4" />
                إعجابات
              </div>
              <div className="text-2xl font-bold text-green-600">
                {summary.total_likes}
              </div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <ThumbsDown className="w-4 h-4" />
                عدم إعجاب
              </div>
              <div className="text-2xl font-bold text-red-600">
                {summary.total_dislikes}
              </div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg shadow">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                <Star className="w-4 h-4" />
                نجوم
              </div>
              <div className="text-2xl font-bold text-yellow-600">
                {summary.total_stars}
              </div>
            </div>
          </div>
        )}

        {/* Tier Selector */}
        <div className="flex gap-2 mb-6">
          {Object.keys(tierNames).map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedTier === tier
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {tierNames[tier]}
            </button>
          ))}
        </div>

        {/* Leaderboard Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-500">
              جاري التحميل...
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    الترتيب
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    الموديل
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    النقاط
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    التقييمات
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    معدل النجاح
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {leaderboards[selectedTier]?.map((item) => (
                  <tr key={item.model_identifier} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Trophy className={`w-5 h-5 ${getMedalColor(item.rank)}`} />
                        <span className="text-lg font-bold text-gray-900">
                          #{item.rank}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {item.model_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {item.model_identifier}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <TrendingUp className="w-4 h-4 text-blue-600" />
                        <span className="text-lg font-bold text-blue-600">
                          {item.score}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-center gap-3 text-sm">
                        <span className="flex items-center gap-1 text-green-600">
                          <ThumbsUp className="w-4 h-4" />
                          {item.total_likes}
                        </span>
                        <span className="flex items-center gap-1 text-red-600">
                          <ThumbsDown className="w-4 h-4" />
                          {item.total_dislikes}
                        </span>
                        <span className="flex items-center gap-1 text-yellow-600">
                          <Star className="w-4 h-4" />
                          {item.total_stars}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {item.success_rate.toFixed(1)}%
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Top Models Summary */}
        {summary?.top_models && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              أفضل موديل في كل مستوى
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(summary.top_models).map(([tier, model]) => (
                <div key={tier} className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg shadow">
                  <div className="text-sm text-gray-600 mb-1">
                    {tierNames[tier]}
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {model.model_name}
                  </div>
                  <div className="text-2xl font-bold text-blue-600 mt-2">
                    {model.score} نقطة
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default LeaderboardPage;
