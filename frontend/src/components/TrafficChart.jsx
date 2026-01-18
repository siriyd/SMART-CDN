import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function TrafficChart({ data, title = 'Traffic Over Time' }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  // Transform data for chart (group by time if needed)
  const chartData = data.map((item, index) => ({
    time: index + 1,
    requests: item.total_requests || 0,
    hits: item.cache_hits || 0,
    misses: item.cache_misses || 0,
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="requests"
            stroke="#3b82f6"
            name="Total Requests"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="hits"
            stroke="#10b981"
            name="Cache Hits"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="misses"
            stroke="#ef4444"
            name="Cache Misses"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrafficChart;
