import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = ['#10b981', '#ef4444']; // Green for hits, Red for misses

function HitMissChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  // Transform data for pie chart
  const chartData = data.map((edge) => ({
    name: edge.region || edge.edge_id,
    hits: edge.cache_hits || 0,
    misses: edge.cache_misses || 0,
    hitRatio: edge.hit_ratio_percent || 0,
  }));

  // Create pie chart data
  const pieData = chartData.map((item) => ({
    name: item.name,
    value: item.hits,
    type: 'Hits',
  })).concat(
    chartData.map((item) => ({
      name: item.name,
      value: item.misses,
      type: 'Misses',
    }))
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Cache Hit/Miss by Edge</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value, type }) => `${name} ${type}: ${value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="mt-4 grid grid-cols-2 gap-4">
        {chartData.map((item) => (
          <div key={item.name} className="text-center">
            <p className="text-sm text-gray-600">{item.name}</p>
            <p className="text-2xl font-bold text-gray-900">{item.hitRatio.toFixed(1)}%</p>
            <p className="text-xs text-gray-500">
              {item.hits} hits / {item.misses} misses
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default HitMissChart;
