import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ExperimentToggle from '../components/ExperimentToggle';
import { experimentsAPI } from '../api/client';
import MetricCard from '../components/MetricCard';

function Experiments() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [experiment, setExperiment] = useState(null);
  const [results, setResults] = useState(null);
  const [experimentsList, setExperimentsList] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadStatus();
    loadExperiments();
    const interval = setInterval(() => {
      loadStatus();
      if (experiment) {
        loadResults();
      }
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [navigate, experiment]);

  useEffect(() => {
    if (experiment) {
      loadResults();
    }
  }, [experiment]);

  const loadStatus = async () => {
    try {
      const status = await experimentsAPI.getStatus();
      setAiEnabled(status.ai_enabled);
      setExperiment(status.experiment);
      setError(null);
    } catch (err) {
      setError('Failed to load experiment status');
      console.error('Error loading status:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadResults = async () => {
    try {
      if (experiment && experiment.experiment_id) {
        const resultsData = await experimentsAPI.getResults(experiment.experiment_id);
        setResults(resultsData);
      }
    } catch (err) {
      console.error('Error loading results:', err);
    }
  };

  const loadExperiments = async () => {
    try {
      const data = await experimentsAPI.list(20);
      setExperimentsList(data.experiments || []);
    } catch (err) {
      console.error('Error loading experiments list:', err);
    }
  };

  const handleToggle = async (newValue) => {
    try {
      const response = await experimentsAPI.toggle(newValue);
      setAiEnabled(newValue);
      setExperiment(response.experiment);
      await loadExperiments();
      alert(`AI mode ${newValue ? 'enabled' : 'disabled'} successfully!`);
    } catch (err) {
      alert('Failed to toggle AI mode');
      console.error('Error toggling experiment:', err);
    }
  };

  const handleCompare = async (aiExpId, baselineExpId) => {
    try {
      const comparisonData = await experimentsAPI.compare(aiExpId, baselineExpId);
      setComparison(comparisonData);
    } catch (err) {
      alert('Failed to compare experiments');
      console.error('Error comparing experiments:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading experiments...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Experiments</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <div className="space-y-6">
          <ExperimentToggle aiEnabled={aiEnabled} onToggle={handleToggle} />

          {/* Current Experiment Results */}
          {results && results.metrics && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Current Experiment Results
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  title="Total Requests"
                  value={results.metrics.total_requests.toLocaleString()}
                  icon="📊"
                />
                <MetricCard
                  title="Cache Hit Ratio"
                  value={results.metrics.cache_hit_ratio.toFixed(1)}
                  unit="%"
                  icon="🎯"
                />
                <MetricCard
                  title="Avg Latency"
                  value={results.metrics.avg_response_time_ms.toFixed(0)}
                  unit="ms"
                  icon="⚡"
                />
                <MetricCard
                  title="Cache Hits"
                  value={results.metrics.cache_hits.toLocaleString()}
                  icon="✅"
                />
              </div>
            </div>
          )}

          {/* A/B Testing Info */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">A/B Testing</h2>
            <p className="text-gray-600 mb-4">
              Compare AI-driven caching performance against baseline (no AI) caching.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border-2 border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-800 mb-2">AI-Enabled Mode</h3>
                <p className="text-sm text-gray-600">
                  AI engine generates prefetch, eviction, and TTL decisions based on
                  popularity predictions.
                </p>
              </div>
              <div className="border-2 border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">Baseline Mode</h3>
                <p className="text-sm text-gray-600">
                  Standard caching with LRU/LFU eviction and fixed TTLs, no AI-driven decisions.
                </p>
              </div>
            </div>
          </div>

          {/* Comparison Results */}
          {comparison && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Experiment Comparison</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="font-semibold text-blue-800 mb-2">AI-Enabled</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Hit Ratio:</span>
                      <span className="font-semibold">
                        {comparison.ai_metrics.cache_hit_ratio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Latency:</span>
                      <span className="font-semibold">
                        {comparison.ai_metrics.avg_response_time_ms.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Baseline</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Hit Ratio:</span>
                      <span className="font-semibold">
                        {comparison.baseline_metrics.cache_hit_ratio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Avg Latency:</span>
                      <span className="font-semibold">
                        {comparison.baseline_metrics.avg_response_time_ms.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800 mb-2">Improvements</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Hit Ratio Improvement:</span>
                    <span className="font-semibold text-green-600 ml-2">
                      +{comparison.improvements.cache_hit_ratio_improvement_pct.toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Latency Improvement:</span>
                    <span className="font-semibold text-green-600 ml-2">
                      {comparison.improvements.latency_improvement_pct.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Experiments List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Experiments</h2>
            {experimentsList.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        AI Enabled
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Start Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {experimentsList.map((exp) => (
                      <tr key={exp.experiment_id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {exp.experiment_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs rounded ${
                              exp.ai_enabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {exp.ai_enabled ? 'AI ON' : 'Baseline'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {exp.start_time
                            ? new Date(exp.start_time).toLocaleString()
                            : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs rounded ${
                              exp.is_active
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {exp.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() => handleCompare(exp.experiment_id, exp.experiment_id)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View Results
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No experiments found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Experiments;
