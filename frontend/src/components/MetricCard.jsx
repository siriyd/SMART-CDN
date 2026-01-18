function MetricCard({ title, value, unit = '', icon, trend, subtitle }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {value}
            {unit && <span className="text-lg text-gray-500 ml-1">{unit}</span>}
          </p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && (
            <p className={`text-sm mt-2 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        {icon && (
          <div className="text-4xl text-blue-500">{icon}</div>
        )}
      </div>
    </div>
  );
}

export default MetricCard;
