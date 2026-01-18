function EdgeMap({ edges, onEdgeClick }) {
  if (!edges || edges.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-500 text-center">No edge nodes available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Edge Node Map</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {edges.map((edge) => (
          <div
            key={edge.edge_id}
            onClick={() => onEdgeClick && onEdgeClick(edge.edge_id)}
            className="border-2 border-blue-200 rounded-lg p-4 hover:border-blue-500 cursor-pointer transition"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-gray-800">{edge.edge_id}</h4>
              <span
                className={`px-2 py-1 rounded text-xs ${
                  edge.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {edge.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-2">Region: {edge.region}</p>
            <div className="mt-3 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Capacity:</span>
                <span className="font-medium">{edge.cache_capacity_mb} MB</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Usage:</span>
                <span className="font-medium">{edge.current_usage_mb} MB</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{
                    width: `${(edge.current_usage_mb / edge.cache_capacity_mb) * 100}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default EdgeMap;
