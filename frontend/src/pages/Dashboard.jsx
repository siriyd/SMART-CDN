import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MetricCard from '../components/MetricCard';
import HitMissChart from '../components/HitMissChart';
import TrafficChart from '../components/TrafficChart';
import { metricsAPI, aiAPI } from '../api/client';

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [navigate]);

  const loadMetrics = async () => {
    try {
      const [hitRatio, latency, popularity, summaryData] = await Promise.all([
        metricsAPI.getCacheHitRatio(),
        metricsAPI.getLatency(),
        metricsAPI.getContentPopularity(10),
        metricsAPI.getMetricsSummary(),
      ]);

      setMetrics({ hitRatio, latency, popularity });
      setSummary(summaryData);
      setError(null);
    } catch (err) {
      setError('Failed to load metrics');
      console.error('Error loading metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerAI = async () => {
    try {
      await aiAPI.triggerDecisions(60, true);
      alert('AI decisions triggered successfully!');
      loadMetrics(); // Refresh metrics
    } catch (err) {
      alert('Failed to trigger AI decisions');
      console.error('Error triggering AI:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  const hitRatioData = Array.isArray(metrics?.hitRatio) ? metrics.hitRatio : (metrics?.hitRatio?.data || []);
  const latencyData = metrics?.latency?.data || [];
  const totalRequests = hitRatioData.reduce((sum, edge) => sum + (edge.total_requests || 0), 0);
  const totalHits = hitRatioData.reduce((sum, edge) => sum + (edge.hits || edge.cache_hits || 0), 0);
  const totalMisses = hitRatioData.reduce((sum, edge) => sum + (edge.misses || edge.cache_misses || 0), 0);
  const avgHitRatio =
    hitRatioData.length > 0
      ? hitRatioData.reduce((sum, edge) => sum + (edge.hit_ratio || edge.hit_ratio_percent || 0), 0) /
        hitRatioData.length
      : 0;
  const avgLatency =
    latencyData.length > 0
      ? latencyData.reduce((sum, edge) => sum + (edge.avg_response_time_ms || 0), 0) /
        latencyData.length
      : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Dashboard Overview</h1>
          <button
            onClick={handleTriggerAI}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Trigger AI Decisions
          </button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Requests"
            value={totalRequests.toLocaleString()}
            icon="📊"
          />
          <MetricCard
            title="Cache Hit Ratio"
            value={avgHitRatio.toFixed(1)}
            unit="%"
            icon="🎯"
            subtitle={`${totalHits} hits / ${totalMisses} misses`}
          />
          <MetricCard
            title="Avg Latency"
            value={avgLatency.toFixed(0)}
            unit="ms"
            icon="⚡"
          />
          <MetricCard
            title="Active Edges"
            value={hitRatioData.length}
            icon="🌐"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <HitMissChart data={hitRatioData} />
          <TrafficChart data={hitRatioData} title="Request Distribution" />
        </div>

        {/* Popular Content */}
        {(() => {
          const popularityData = Array.isArray(metrics?.popularity) ? metrics.popularity : (metrics?.popularity?.data || []);
          return popularityData.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Top Popular Content</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Content ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Requests
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Hit Ratio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Avg Latency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {popularityData.slice(0, 10).map((content) => (
                    <tr key={content.content_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {content.content_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {content.content_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {content.total_requests}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {(content.hit_ratio || content.hit_ratio_percent || 0).toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {(content.avg_response_time_ms || 0).toFixed(0)}ms
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          );
        })()}
      </div>
    </div>
  );
}

export default Dashboard;
