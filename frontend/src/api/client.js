/**
 * API Client for Smart CDN Backend
 * Handles all HTTP requests to the backend API
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
  
  verifyToken: async (token) => {
    const response = await apiClient.post('/auth/verify', { token });
    return response.data;
  },
};

// Metrics API
export const metricsAPI = {
  getCacheHitRatio: async () => {
    const response = await apiClient.get('/metrics/cache-hit-ratio');
    return response.data;
  },
  
  getLatency: async () => {
    const response = await apiClient.get('/metrics/latency');
    return response.data;
  },
  
  getContentPopularity: async (limit = 20) => {
    const response = await apiClient.get('/metrics/popularity', {
      params: { limit },
    });
    return response.data;
  },
  
  getMetricsSummary: async () => {
    const response = await apiClient.get('/metrics/summary');
    return response.data;
  },
};

// AI Decisions API
export const aiAPI = {
  triggerDecisions: async (timeWindowMinutes = 60, applyDecisions = true) => {
    const response = await apiClient.post('/ai/decide', null, {
      params: {
        time_window_minutes: timeWindowMinutes,
        apply_decisions: applyDecisions,
      },
    });
    return response.data;
  },
  
  getDecisions: async (limit = 50) => {
    const response = await apiClient.get('/ai/decisions', {
      params: { limit },
    });
    return response.data;
  },
};

// Edges API
export const edgesAPI = {
  getEdges: async () => {
    const response = await apiClient.get('/edges');
    return response.data;
  },
  
  getEdge: async (edgeId) => {
    const response = await apiClient.get(`/edges/${edgeId}`);
    return response.data;
  },
  
  getEdgeStats: async (edgeId) => {
    const response = await apiClient.get(`/edges/${edgeId}/stats`);
    return response.data;
  },
};

// Requests API
export const requestsAPI = {
  getRequests: async (limit = 100, edgeId = null, contentId = null) => {
    const response = await apiClient.get('/requests', {
      params: { limit, edge_id: edgeId, content_id: contentId },
    });
    return response.data;
  },
};

// Content API
export const contentAPI = {
  getContent: async (limit = 50, category = null, contentType = null) => {
    const response = await apiClient.get('/content', {
      params: { limit, category, content_type: contentType },
    });
    return response.data;
  },
  
  getPopularContent: async (limit = 20) => {
    const response = await apiClient.get('/content/popular', {
      params: { limit },
    });
    return response.data;
  },
};

// Experiments API
export const experimentsAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/experiments/status');
    return response.data;
  },
  
  toggle: async (aiEnabled) => {
    const response = await apiClient.post('/experiments/toggle', {
      ai_enabled: aiEnabled,
    });
    return response.data;
  },
  
  getResults: async (experimentId = null) => {
    const params = experimentId ? { experiment_id: experimentId } : {};
    const response = await apiClient.get('/experiments/results', { params });
    return response.data;
  },
  
  compare: async (aiExperimentId, baselineExperimentId) => {
    const response = await apiClient.get('/experiments/compare', {
      params: {
        ai_experiment_id: aiExperimentId,
        baseline_experiment_id: baselineExperimentId,
      },
    });
    return response.data;
  },
  
  list: async (limit = 10) => {
    const response = await apiClient.get('/experiments/list', {
      params: { limit },
    });
    return response.data;
  },
};

export default apiClient;
