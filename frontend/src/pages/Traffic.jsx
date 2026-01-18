import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestsAPI, metricsAPI } from '../api/client';
import TrafficChart from '../components/TrafficChart';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

function Traffic() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);
  const [popularity, setPopularity] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [navigate]);

  const loadData = async () => {
    try {
      const [requestsData, popularityData] = await Promise.all([
        requestsAPI.getRequests(100),
        metricsAPI.getContentPopularity(20),
      ]);

      setRequests(requestsData.data || []);
      setPopularity(popularityData.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to load traffic data');
      console.error('Error loading traffic:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading traffic data...</p>
        </div>
      </div>
    );
  }

  // Group requests by time (last hour)
  const now = new Date();
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  const recentRequests = requests.filter((req) => {
    const reqTime = new Date(req.request_timestamp);
    return reqTime >= oneHourAgo;
  });

  // Group by 5-minute intervals
  const timeGroups = {};
  recentRequests.forEach((req) => {
    const reqTime = new Date(req.request_timestamp);
    const minutes = Math.floor(reqTime.getMinutes() / 5) * 5;
    const timeKey = `${reqTime.getHours()}:${minutes.toString().padStart(2, '0')}`;
    if (!timeGroups[timeKey]) {
      timeGroups[timeKey] = { time: timeKey, requests: 0, hits: 0, misses: 0 };
    }
    timeGroups[timeKey].requests++;
    if (req.is_cache_hit) {
      timeGroups[timeKey].hits++;
    } else {
      timeGroups[timeKey].misses++;
    }
  });

  const timeSeriesData = Object.values(timeGroups).sort((a, b) =>
    a.time.localeCompare(b.time)
  );

  // Content popularity chart data
  const popularityChartData = popularity.slice(0, 10).map((item) => ({
    name: item.content_id,
    requests: item.total_requests || 0,
    'Last Hour': item.requests_last_hour || 0,
    'Last 24h': item.requests_last_24h || 0,
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Traffic Patterns</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Traffic Over Time */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Request Traffic (Last Hour)
          </h2>
          {timeSeriesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  name="Total Requests"
                />
                <Area
                  type="monotone"
                  dataKey="hits"
                  stackId="2"
                  stroke="#10b981"
                  fill="#10b981"
                  name="Cache Hits"
                />
                <Area
                  type="monotone"
                  dataKey="misses"
                  stackId="2"
                  stroke="#ef4444"
                  fill="#ef4444"
                  name="Cache Misses"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No recent traffic data</p>
          )}
        </div>

        {/* Content Popularity */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Content Popularity</h2>
          {popularityChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={popularityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="requests" fill="#3b82f6" name="Total Requests" />
                <Bar dataKey="Last Hour" fill="#10b981" name="Last Hour" />
                <Bar dataKey="Last 24h" fill="#60a5fa" name="Last 24h" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No popularity data available</p>
          )}
        </div>

        {/* Recent Requests Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Requests</h2>
          {requests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No requests found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Content ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Edge ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Cache Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Response Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {requests.slice(0, 50).map((req) => (
                    <tr key={req.request_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(req.request_timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {req.content_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {req.edge_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            req.is_cache_hit
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {req.is_cache_hit ? 'HIT' : 'MISS'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {req.response_time_ms}ms
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

export default Traffic;

