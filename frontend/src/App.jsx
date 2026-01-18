import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AIDecisions from './pages/AIDecisions';
import CachePerformance from './pages/CachePerformance';
import EdgeNodes from './pages/EdgeNodes';
import Traffic from './pages/Traffic';
import Predictions from './pages/Predictions';
import Experiments from './pages/Experiments';

// Protected Route component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('auth_token');
  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {isAuthenticated && <Navbar />}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai-decisions"
            element={
              <ProtectedRoute>
                <AIDecisions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cache-performance"
            element={
              <ProtectedRoute>
                <CachePerformance />
              </ProtectedRoute>
            }
          />
          <Route
            path="/edge-nodes"
            element={
              <ProtectedRoute>
                <EdgeNodes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/traffic"
            element={
              <ProtectedRoute>
                <Traffic />
              </ProtectedRoute>
            }
          />
          <Route
            path="/predictions"
            element={
              <ProtectedRoute>
                <Predictions />
              </ProtectedRoute>
            }
          />
          <Route
            path="/experiments"
            element={
              <ProtectedRoute>
                <Experiments />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
