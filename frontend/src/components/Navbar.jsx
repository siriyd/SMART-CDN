import { Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { authAPI } from '../api/client';

function Navbar() {
  const navigate = useNavigate();
  const [username, setUsername] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      authAPI.getCurrentUser()
        .then((user) => setUsername(user.username))
        .catch(() => {
          localStorage.removeItem('auth_token');
          navigate('/login');
        });
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    navigate('/login');
  };

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link to="/dashboard" className="text-xl font-bold">
              Smart CDN Dashboard
            </Link>
            <div className="flex space-x-4">
              <Link
                to="/dashboard"
                className="hover:bg-blue-700 px-3 py-2 rounded transition"
              >
                Dashboard
              </Link>
              <Link
                to="/ai-decisions"
                className="hover:bg-blue-700 px-3 py-2 rounded transition"
              >
                AI Decisions
              </Link>
              <Link
                to="/cache-performance"
                className="hover:bg-blue-700 px-3 py-2 rounded transition"
              >
                Cache Performance
              </Link>
              <Link
                to="/edge-nodes"
                className="hover:bg-blue-700 px-3 py-2 rounded transition"
              >
                Edge Nodes
              </Link>
              <Link
                to="/traffic"
                className="hover:bg-blue-700 px-3 py-2 rounded transition"
              >
                Traffic
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {username && (
              <span className="text-sm">Welcome, {username}</span>
            )}
            <button
              onClick={handleLogout}
              className="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
