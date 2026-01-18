import { useState } from 'react';

function ExperimentToggle({ aiEnabled, onToggle }) {
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    setLoading(true);
    try {
      await onToggle(!aiEnabled);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">AI Engine Status</h3>
          <p className="text-sm text-gray-600 mt-1">
            {aiEnabled
              ? 'AI-driven caching is enabled'
              : 'AI-driven caching is disabled (baseline mode)'}
          </p>
        </div>
        <button
          onClick={handleToggle}
          disabled={loading}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            aiEnabled ? 'bg-blue-600' : 'bg-gray-300'
          } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              aiEnabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
      {loading && (
        <p className="text-sm text-gray-500 mt-2">Updating...</p>
      )}
    </div>
  );
}

export default ExperimentToggle;
