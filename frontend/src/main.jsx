import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import './index.css'

// Ensure root element exists
console.log('🎬 main.jsx - Starting application...');
const rootElement = document.getElementById('root');

if (!rootElement) {
  console.error('❌ Root element not found!');
  throw new Error('Root element not found! Make sure index.html has a div with id="root"');
}

console.log('✅ Root element found:', rootElement);

// Create root only once
try {
  console.log('🏗️ Creating React root...');
  const root = ReactDOM.createRoot(rootElement);
  console.log('✅ React root created successfully');
  
  console.log('🎨 Rendering app...');
  root.render(
    <ErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  );
  console.log('✅ App rendered successfully');
} catch (error) {
  console.error('❌ Failed to render app:', error);
  console.error('Failed to create React root:', error);
  // Fallback: show error message
  rootElement.innerHTML = `
    <div style="padding: 40px; text-align: center; font-family: Arial;">
      <h1 style="color: red;">❌ Failed to load application</h1>
      <p>An error occurred while initializing React. Please:</p>
      <ul style="text-align: right; max-width: 500px; margin: 20px auto;">
        <li>Temporarily disable browser extensions</li>
        <li>Clear browser cache (Ctrl+Shift+Delete)</li>
        <li>Open the page in Incognito mode</li>
      </ul>
      <button onclick="location.reload()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-top: 20px;">
        🔄 Retry
      </button>
      <details style="margin-top: 20px; text-align: left;">
        <summary style="cursor: pointer;">Technical Details</summary>
        <pre style="background: #f5f5f5; padding: 15px; overflow: auto;">${error.toString()}</pre>
      </details>
    </div>
  `;
}
