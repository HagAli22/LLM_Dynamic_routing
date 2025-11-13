import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatbotPage from './pages/ChatbotPage';
import DashboardPage from './pages/DashboardPage';
import BatchProcessingPage from './pages/BatchProcessingPage';
import SettingsPage from './pages/SettingsPage';
import TestPage from './pages/TestPage';
import Layout from './components/Layout';
import { authAPI } from './services/api';

function App() {
  const [user, setUser] = useState(() => {
    // Initialize user from localStorage if available
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch (e) {
        console.error('Failed to parse saved user:', e);
        return null;
      }
    }
    return null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Prevent multiple calls
    let mounted = true;
    console.log('🚀 App useEffect - Starting initialization');
    const init = async () => {
      if (mounted) {
        console.log('🔍 Checking authentication...');
        await checkAuth();
      }
    };
    init();
    
    // Listen for auth:logout event from API interceptor
    const handleAuthLogout = () => {
      console.log('🔔 Received auth:logout event');
      if (mounted) {
        setUser(null);
      }
    };
    
    window.addEventListener('auth:logout', handleAuthLogout);
    
    return () => { 
      console.log('🧹 App cleanup');
      mounted = false;
      window.removeEventListener('auth:logout', handleAuthLogout);
    };
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('🔑 Token found:', token ? 'Yes' : 'No');
      
      if (token) {
        console.log('⏳ Fetching current user...');
        // Add timeout to prevent infinite loading
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 5000)
        );
        
        const response = await Promise.race([
          authAPI.getCurrentUser(),
          timeoutPromise
        ]);
        
        console.log('✅ User authenticated:', response.data);
        // Save to both state and localStorage
        localStorage.setItem('user', JSON.stringify(response.data));
        setUser(response.data);
      } else {
        console.log('❌ No token - user not authenticated');
        setUser(null);
        localStorage.removeItem('user');
      }
    } catch (error) {
      console.error('❌ Auth check failed:', error);
      // Clear everything on auth failure
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    } finally {
      console.log('✔️ Setting loading to false');
      setLoading(false);
    }
  };

  const handleLogout = () => {
    console.log('🚪 Logging out...');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    console.log('⏳ Rendering loading screen...');
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">جاري التحميل...</p>
        </div>
      </div>
    );
  }

  console.log('🎨 Rendering main app, user:', user ? 'Logged in' : 'Not logged in');

  return (
    <Routes>
      <Route path="/test" element={<TestPage />} />
      <Route path="/login" element={!user ? <LoginPage setUser={setUser} /> : <Navigate to="/chatbot" replace />} />
      <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/chatbot" replace />} />
      
      <Route element={user ? <Layout user={user} onLogout={handleLogout} /> : <Navigate to="/login" replace />}>
        <Route path="/chatbot" element={<ChatbotPage user={user} />} />
        <Route path="/dashboard" element={<DashboardPage user={user} />} />
        <Route path="/batch" element={<BatchProcessingPage user={user} />} />
        <Route path="/settings" element={<SettingsPage user={user} />} />
      </Route>
      
      <Route path="/" element={<Navigate to={user ? "/chatbot" : "/login"} replace />} />
      {/* Catch-all route for any unmatched paths */}
      <Route path="*" element={<Navigate to={user ? "/chatbot" : "/login"} replace />} />
    </Routes>
  );
}

export default App;
