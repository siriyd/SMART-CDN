import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { metricsAPI } from '../api/client';
import HitMissChart from '../components/HitMissChart';
import TrafficChart from '../components/TrafficChart';
import MetricCard from '../components/MetricCard';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

function CachePerformance() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hitRatioData, setHitRatioData] = useState([]);
  const [latencyData, setLatencyData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadMetrics();
    const interval = setInterval(loadMetrics, 30000);
    return () => clearInterval(interval);
  }, [navigate]);

  const loadMetrics = async () => {
    try {
      const [hitRatio, latency] = await Promise.all([
        metricsAPI.getCacheHitRatio(),
        metricsAPI.getLatency(),
      ]);

      setHitRatioData(Array.isArray(hitRatio) ? hitRatio : (hitRatio.data || []));
      setLatencyData(latency.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load cache performance metrics');
      console.error('Error loading metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading cache performance data...</p>
        </div>
      </div>
    );
  }

  const totalHits = hitRatioData.reduce((sum, edge) => sum + (edge.hits || edge.cache_hits || 0), 0);
  const totalMisses = hitRatioData.reduce((sum, edge) => sum + (edge.misses || edge.cache_misses || 0), 0);
  const avgHitRatio =
    hitRatioData.length > 0
      ? hitRatioData.reduce((sum, edge) => sum + (edge.hit_ratio || edge.hit_ratio_percent || 0), 0) /
        hitRatioData.length
      : 0;
  const avgHitLatency =
    latencyData.length > 0
      ? latencyData.reduce((sum, edge) => sum + (edge.avg_hit_latency_ms || 0), 0) /
        latencyData.length
      : 0;
  const avgMissLatency =
    latencyData.length > 0
      ? latencyData.reduce((sum, edge) => sum + (edge.avg_miss_latency_ms || 0), 0) /
        latencyData.length
      : 0;

  const barChartData = hitRatioData.map((edge) => ({
    name: edge.region || edge.edge_id,
    'Hit Ratio %': edge.hit_ratio || edge.hit_ratio_percent || 0,
    'Hit Latency (ms)': edge.avg_hit_latency_ms || 0,
    'Miss Latency (ms)': edge.avg_miss_latency_ms || 0,
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Cache Performance</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Overall Hit Ratio"
            value={avgHitRatio.toFixed(1)}
            unit="%"
            icon="🎯"
          />
          <MetricCard
            title="Total Hits"
            value={totalHits.toLocaleString()}
            icon="✅"
          />
          <MetricCard
            title="Total Misses"
            value={totalMisses.toLocaleString()}
            icon="❌"
          />
          <MetricCard
            title="Latency Improvement"
            value={(avgMissLatency - avgHitLatency).toFixed(0)}
            unit="ms"
            icon="⚡"
            subtitle={`${avgHitLatency.toFixed(0)}ms hit vs ${avgMissLatency.toFixed(0)}ms miss`}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <HitMissChart data={hitRatioData} />
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Hit Ratio by Edge
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Hit Ratio %" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Comparison */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Latency Comparison: Cache Hit vs Miss
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Hit Latency (ms)" fill="#10b981" name="Cache Hit" />
              <Bar dataKey="Miss Latency (ms)" fill="#ef4444" name="Cache Miss" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Edge Performance Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Edge Performance Details</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Edge ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Region
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Hit Ratio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Total Requests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Hits
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Misses
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Avg Latency
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {hitRatioData.map((edge) => (
                  <tr key={edge.edge_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {edge.edge_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {edge.region}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span
                        className={`font-semibold ${
                          ((edge.hit_ratio || edge.hit_ratio_percent) || 0) > 70
                            ? 'text-green-600'
                            : ((edge.hit_ratio || edge.hit_ratio_percent) || 0) > 50
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {((edge.hit_ratio || edge.hit_ratio_percent) || 0).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {edge.total_requests || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                      {edge.hits || edge.cache_hits || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {edge.misses || edge.cache_misses || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(edge.avg_response_time_ms || 0).toFixed(0)}ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CachePerformance;

