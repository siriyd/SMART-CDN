import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { aiAPI } from '../api/client';
import MetricCard from '../components/MetricCard';

function AIDecisions() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [decisions, setDecisions] = useState([]);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadDecisions();
    const interval = setInterval(loadDecisions, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [navigate]);

  const loadDecisions = async () => {
    try {
      const response = await aiAPI.getDecisions(50);
      setDecisions(response.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load AI decisions');
      console.error('Error loading decisions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const result = await aiAPI.triggerDecisions(60, true);
      alert(`AI decisions triggered! Generated ${result.decisions?.prefetch_plan?.length || 0} prefetch decisions.`);
      loadDecisions(); // Refresh
    } catch (err) {
      alert('Failed to trigger AI decisions');
      console.error('Error triggering AI:', err);
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading AI decisions...</p>
        </div>
      </div>
    );
  }

  const prefetchCount = decisions.filter((d) => d.decision_type === 'prefetch').length;
  const evictCount = decisions.filter((d) => d.decision_type === 'evict').length;
  const ttlUpdateCount = decisions.filter((d) => d.decision_type === 'ttl_update').length;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">AI Decisions</h1>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            {triggering ? 'Triggering...' : 'Trigger AI Decisions'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MetricCard
            title="Prefetch Decisions"
            value={prefetchCount}
            icon="⬇️"
            subtitle="Content to prefetch"
          />
          <MetricCard
            title="Eviction Decisions"
            value={evictCount}
            icon="🗑️"
            subtitle="Content to evict"
          />
          <MetricCard
            title="TTL Updates"
            value={ttlUpdateCount}
            icon="⏱️"
            subtitle="TTL adjustments"
          />
        </div>

        {/* Decisions Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Decisions</h2>
          {decisions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No AI decisions found. Trigger decisions to see results.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Decision ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Content ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Edge ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Applied
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {decisions.map((decision) => (
                    <tr key={decision.decision_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {decision.decision_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            decision.decision_type === 'prefetch'
                              ? 'bg-green-100 text-green-800'
                              : decision.decision_type === 'evict'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {decision.decision_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {decision.content_id || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {decision.edge_id || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {decision.priority || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {decision.decision_timestamp
                          ? new Date(decision.decision_timestamp).toLocaleString()
                          : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {decision.applied_at ? (
                          <span className="text-green-600 text-sm">✓ Applied</span>
                        ) : (
                          <span className="text-gray-400 text-sm">Pending</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIDecisions;

