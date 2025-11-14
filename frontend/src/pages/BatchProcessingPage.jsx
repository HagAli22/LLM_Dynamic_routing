import { useState } from 'react';
import { queriesAPI } from '../services/api';
import { Upload, Download, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function BatchProcessingPage() {
  const [queries, setQueries] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const queryList = queries.split('\n').map(q => q.trim()).filter(q => q.length > 0);

    if (queryList.length === 0 || queryList.length > 100) {
      alert(queryList.length === 0 ? 'Enter at least one query' : 'Maximum 100 queries');
      return;
    }

    setLoading(true);
    try {
      const response = await queriesAPI.processBatch({ queries: queryList, skip_cache: false });
      setResults(response.data);
    } catch (error) {
      alert(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!results) return;
    const headers = ['Query', 'Response', 'Classification', 'Tier', 'Model', 'Time', 'Cache'];
    const rows = results.results.map(r => [
      `"${r.query.replace(/"/g, '""')}"`,
      `"${r.response.replace(/"/g, '""')}"`,
      r.classification, r.model_tier, r.used_model,
      r.processing_time.toFixed(2), r.cache_hit ? 'Yes' : 'No'
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `results_${Date.now()}.csv`;
    link.click();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6" dir="rtl">
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-2xl">
        <h1 className="text-3xl font-bold mb-2">Batch Processing</h1>
        <p className="text-purple-100">Process multiple queries in one batch</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={queries}
            onChange={(e) => setQueries(e.target.value)}
            placeholder="Enter each query on a new line..."
            rows={10}
            className="w-full px-4 py-3 border rounded-xl dark:bg-gray-700 dark:text-white"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl disabled:opacity-50"
          >
            {loading ? <><Loader2 className="inline animate-spin ml-2" /> Processing...</> : 'Process Queries'}
          </button>
        </form>
      </div>

      {results && (
        <>
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-3xl font-bold">{results.total_queries}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <p className="text-sm text-gray-600">Successful</p>
              <p className="text-3xl font-bold text-green-600">{results.successful}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <p className="text-sm text-gray-600">Failed</p>
              <p className="text-3xl font-bold text-red-600">{results.failed}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg">
              <p className="text-sm text-gray-600">Time</p>
              <p className="text-3xl font-bold text-purple-600">{results.total_processing_time.toFixed(2)}s</p>
            </div>
          </div>

          <button onClick={exportToCSV} className="px-6 py-3 bg-green-600 text-white rounded-xl">
            <Download className="inline h-5 w-5 ml-2" /> Export CSV
          </button>

          <div className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-right text-xs font-semibold">#</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold">Query</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold">Answer</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold">Classification</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold">Time</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold">Cache</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-gray-700">
                  {results.results.map((r, i) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 text-sm">{i + 1}</td>
                      <td className="px-6 py-4 text-sm max-w-xs truncate">{r.query}</td>
                      <td className="px-6 py-4 text-sm max-w-md truncate">{r.response}</td>
                      <td className="px-6 py-4"><span className="px-2 py-1 text-xs rounded-full bg-blue-100">{r.classification}</span></td>
                      <td className="px-6 py-4 text-sm">{r.processing_time.toFixed(2)}s</td>
                      <td className="px-6 py-4">{r.cache_hit ? '✅' : '❌'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
