# Dynamic LLM Router - Frontend

Modern React frontend for the Dynamic LLM Routing System. Built with React, Vite, and Tailwind CSS for a responsive and intuitive user experience.

## 🌟 Features

### Core Components
- **Dashboard**: Real-time statistics and query monitoring
- **Smart Chatbot**: Interactive chat interface with model rating
- **Settings Page**: API key management and user preferences
- **Leaderboard**: Model rankings based on user feedback
- **Batch Processing**: Process multiple queries simultaneously
- **User Authentication**: Secure login and registration system

### UI/UX Features
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark Mode**: Automatic dark/light theme switching
- **Real-time Updates**: Live status updates and notifications
- **Interactive Charts**: Visual representation of statistics
- **Smooth Animations**: Modern transitions and micro-interactions
- **Accessibility**: WCAG compliant with keyboard navigation

## 🛠️ Technology Stack

### Core Framework
- **React 18**: Modern React with hooks and concurrent features
- **Vite**: Fast build tool and development server
- **JavaScript ES6+**: Modern JavaScript features

### Styling & UI
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Modern icon library
- **Headless UI**: Accessible UI components

### State Management
- **React Context**: Global state management
- **React Query**: Server state management and caching

### HTTP & API
- **Axios**: HTTP client with interceptors
- **React Router**: Client-side routing
- **React Hook Form**: Form handling with validation

### Development Tools
- **ESLint**: Code linting and formatting
- **Prettier**: Code formatting
- **Vitest**: Unit testing framework
- **Testing Library**: Component testing

## 📦 Installation

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Setup
```bash
# Clone the repository (if not already done)
git clone https://github.com/HagAli22/LLM_Dynamic_routing.git
cd LLM_Dynamic_routing/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
```

## 🚀 Development

### Available Scripts
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix
```

### Environment Variables
Create `.env.local` in the frontend root:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Feature Flags
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=false

# Development
VITE_DEV_MODE=true
```

## 🏗️ Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── components/         # Reusable components
│   │   ├── Layout.jsx      # Main layout component
│   │   ├── ModelRating.jsx # Model rating component
│   │   ├── ErrorBoundary.jsx # Error handling
│   │   └── ChatHistorySidebar.jsx # Chat history
│   ├── pages/              # Page components
│   │   ├── DashboardPage.jsx
│   │   ├── ChatbotPage.jsx
│   │   ├── SettingsPage.jsx
│   │   ├── LeaderboardPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   └── BatchProcessingPage.jsx
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API services
│   ├── utils/              # Utility functions
│   ├── styles/             # Global styles
│   ├── App.jsx             # Main App component
│   └── main.jsx            # Entry point
├── package.json
├── vite.config.js
├── tailwind.config.js
└── eslint.config.js
```

## 🔧 Configuration

### Vite Configuration
`vite.config.js` contains build and development settings:

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### Tailwind CSS Configuration
`tailwind.config.js` contains theme and plugin settings:

```javascript
export default {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#8b5cf6',
      },
    },
  },
  plugins: [],
};
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage
```

## 🚀 Deployment

### Build for Production
```bash
# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔍 Debugging

### Development Tools
- **React DevTools**: Component inspection and debugging
- **Network Tab**: API request monitoring
- **Console**: Error and log monitoring

### Common Issues
1. **CORS Errors**: Ensure backend allows frontend origin
2. **Build Failures**: Check for missing dependencies or syntax errors
3. **Route Not Found**: Verify React Router configuration
4. **API Errors**: Check network connectivity and backend status

## 📈 Performance Optimization

### Code Splitting
```javascript
// Lazy load components
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ChatbotPage = lazy(() => import('./pages/ChatbotPage'));

// Use Suspense for loading states
<Suspense fallback={<div>Loading...</div>}>
  <Routes>
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/chatbot" element={<ChatbotPage />} />
  </Routes>
</Suspense>
```

## 🤝 Contributing

### Code Style
- Use ESLint and Prettier for consistent formatting
- Follow React best practices and hooks rules
- Write meaningful component and function names
- Add PropTypes for type safety

### Pull Request Process
1. Create feature branch from main
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation
5. Submit pull request with clear description

## 📄 License

This frontend is part of the Dynamic LLM Router project, licensed under the MIT License.

---

**Built with ❤️ using React and modern web technologies**
