import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Request with token:', config.method.toUpperCase(), config.url);
    } else {
      console.log('⚠️ Request WITHOUT token:', config.method.toUpperCase(), config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Success:', response.config.method.toUpperCase(), response.config.url, response.status);
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.config?.method?.toUpperCase(), error.config?.url, error.response?.status);
    
    if (error.response?.status === 401) {
      console.warn('🚨 401 Unauthorized - Token invalid or expired');
      
      // Only clear auth data and dispatch event
      // Let React Router handle the redirect
      const currentPath = window.location.pathname;
      console.log('📍 Current path:', currentPath);
      
      if (currentPath !== '/login' && currentPath !== '/register') {
        console.log('🔄 Clearing auth data and dispatching logout event...');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        
        // Dispatch custom event to notify App component
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
    }
    return Promise.reject(error);
  }
);

// ==================== AUTH ====================
export const authAPI = {
  register: (userData) => api.post('/api/auth/register', userData),
  login: (credentials) => api.post('/api/auth/login', new URLSearchParams(credentials), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
  getCurrentUser: () => api.get('/api/auth/me'),
};

// ==================== API KEYS ====================
export const apiKeysAPI = {
  getAll: () => api.get('/api/keys'),
  create: (keyData) => api.post('/api/keys', keyData),
  delete: (keyId) => api.delete(`/api/keys/${keyId}`),
};

// ==================== QUERIES ====================
export const queriesAPI = {
  processQuery: (queryData) => api.post('/api/query', queryData),
  processBatch: (batchData) => api.post('/api/query/batch', batchData),
  getHistory: (params) => api.get('/api/queries', { params }),
};

// ==================== PROMPTS ====================
export const promptsAPI = {
  getSuggestions: (prompt) => api.post('/api/prompt/suggest', { prompt }),
  classify: (prompt) => api.post('/api/prompt/classify', { prompt }),
};

// ==================== FEEDBACK ====================
export const feedbackAPI = {
  submit: (feedbackData) => api.post('/api/feedback', feedbackData),
};

// ==================== STATISTICS ====================
export const statsAPI = {
  getUserStats: () => api.get('/api/stats/user'),
  getSystemStats: () => api.get('/api/stats/system'),
};

// ==================== CONVERSATIONS ====================
export const conversationsAPI = {
  getAll: (params) => api.get('/api/conversations', { params }),
  create: (data) => api.post('/api/conversations', data),
  getById: (id) => api.get(`/api/conversations/${id}`),
  update: (id, data) => api.put(`/api/conversations/${id}`, data),
  delete: (id) => api.delete(`/api/conversations/${id}`),
  sendMessage: (conversationId, messageData) => api.post(`/api/conversations/${conversationId}/messages`, messageData),
};

// ==================== HEALTH ====================
export const healthAPI = {
  check: () => api.get('/api/health'),
};

export default api;
