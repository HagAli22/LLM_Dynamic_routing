import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ hasError: true, error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', fontFamily: 'Arial', direction: 'rtl' }}>
          <h1 style={{ color: 'red', fontSize: '32px' }}>❌ An error occurred in the application</h1>
          <div style={{ background: '#fff3cd', padding: '20px', marginTop: '20px', borderRadius: '8px' }}>
            <h2>Error Details:</h2>
            <pre style={{ background: '#f8f9fa', padding: '15px', overflow: 'auto', direction: 'ltr' }}>
              {this.state.error && this.state.error.toString()}
            </pre>
            {this.state.errorInfo && (
              <details style={{ marginTop: '10px' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Stack Trace</summary>
                <pre style={{ background: '#f8f9fa', padding: '15px', overflow: 'auto', fontSize: '12px', direction: 'ltr' }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '20px', padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
          >
            🔄 Reload the page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
