import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { edgesAPI } from '../api/client';
import EdgeMap from '../components/EdgeMap';
import MetricCard from '../components/MetricCard';

function EdgeNodes() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [edges, setEdges] = useState([]);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [edgeStats, setEdgeStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadEdges();
    const interval = setInterval(loadEdges, 30000);
    return () => clearInterval(interval);
  }, [navigate]);

  useEffect(() => {
    if (selectedEdge) {
      loadEdgeStats(selectedEdge);
    }
  }, [selectedEdge]);

  const loadEdges = async () => {
    try {
      const response = await edgesAPI.getEdges();
      setEdges(response.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load edge nodes');
      console.error('Error loading edges:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEdgeStats = async (edgeId) => {
    try {
      const response = await edgesAPI.getEdgeStats(edgeId);
      setEdgeStats(response.data);
    } catch (err) {
      console.error('Error loading edge stats:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading edge nodes...</p>
        </div>
      </div>
    );
  }

  const activeEdges = edges.filter((e) => e.is_active).length;
  const totalCapacity = edges.reduce((sum, e) => sum + (e.cache_capacity_mb || 0), 0);
  const totalUsage = edges.reduce((sum, e) => sum + (e.current_usage_mb || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Edge Nodes</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Edges"
            value={edges.length}
            icon="🌐"
          />
          <MetricCard
            title="Active Edges"
            value={activeEdges}
            icon="✅"
          />
          <MetricCard
            title="Total Capacity"
            value={totalCapacity}
            unit="MB"
            icon="💾"
          />
          <MetricCard
            title="Total Usage"
            value={totalUsage}
            unit="MB"
            icon="📊"
            subtitle={`${((totalUsage / totalCapacity) * 100).toFixed(1)}% utilized`}
          />
        </div>

        {/* Edge Map */}
        <div className="mb-8">
          <EdgeMap edges={edges} onEdgeClick={setSelectedEdge} />
        </div>

        {/* Selected Edge Stats */}
        {selectedEdge && edgeStats && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Statistics for {selectedEdge}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {edgeStats.cache_hit_ratio && (
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Cache Hit Ratio</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Hit Ratio:</span>
                      <span className="font-semibold">
                        {edgeStats.cache_hit_ratio.hit_ratio_percent?.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Requests:</span>
                      <span>{edgeStats.cache_hit_ratio.total_requests || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Cache Hits:</span>
                      <span className="text-green-600">
                        {edgeStats.cache_hit_ratio.cache_hits || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Cache Misses:</span>
                      <span className="text-red-600">
                        {edgeStats.cache_hit_ratio.cache_misses || 0}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              {edgeStats.latency && (
                <div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">Latency Metrics</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Response Time:</span>
                      <span className="font-semibold">
                        {edgeStats.latency.avg_response_time_ms?.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Hit Latency:</span>
                      <span className="text-green-600">
                        {edgeStats.latency.avg_hit_latency_ms?.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Miss Latency:</span>
                      <span className="text-red-600">
                        {edgeStats.latency.avg_miss_latency_ms?.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Edge Details Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">All Edge Nodes</h2>
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
                    Capacity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Usage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Utilization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {edges.map((edge) => {
                  const utilization =
                    edge.cache_capacity_mb > 0
                      ? (edge.current_usage_mb / edge.cache_capacity_mb) * 100
                      : 0;
                  return (
                    <tr
                      key={edge.edge_id}
                      onClick={() => setSelectedEdge(edge.edge_id)}
                      className="cursor-pointer hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {edge.edge_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {edge.region}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {edge.cache_capacity_mb} MB
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {edge.current_usage_mb} MB
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                utilization > 80
                                  ? 'bg-red-600'
                                  : utilization > 60
                                  ? 'bg-yellow-600'
                                  : 'bg-green-600'
                              }`}
                              style={{ width: `${Math.min(utilization, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">{utilization.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            edge.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {edge.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EdgeNodes;
