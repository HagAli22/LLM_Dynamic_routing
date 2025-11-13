# Frontend - React Application

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Structure

```
src/
├── components/       # Reusable components
│   └── Layout.jsx   # Main layout with sidebar
├── pages/           # Page components
│   ├── LoginPage.jsx
│   ├── RegisterPage.jsx
│   ├── ChatbotPage.jsx
│   ├── DashboardPage.jsx
│   ├── BatchProcessingPage.jsx
│   └── SettingsPage.jsx
├── services/        # API services
│   └── api.js      # Axios configuration & API calls
├── App.jsx         # Main app component
├── main.jsx        # Entry point
└── index.css       # Global styles
```

## 🎨 Features

- **RTL Support** (Arabic-friendly)
- **Dark Mode Ready**
- **Responsive Design**
- **Modern UI** (TailwindCSS + shadcn/ui inspired)
- **Smooth Animations**

## 🔧 Configuration

### API Base URL

Edit `src/services/api.js`:

```js
const API_BASE_URL = 'http://localhost:8000';
```

### Theme Colors

Edit `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: 'hsl(221.2 83.2% 53.3%)',
      // ...
    }
  }
}
```

## 📱 Pages

### Login/Register
- JWT Authentication
- Form validation
- Error handling

### Chatbot
- Real-time chat interface
- Prompt suggestions for unclear queries
- Feedback system (rating)
- Metadata display (classification, tier, time, cost)

### Dashboard
- Single query processing
- Classification preview
- Detailed results
- Usage statistics

### Batch Processing
- Multiple queries (up to 100)
- CSV export
- Progress tracking
- Results table

### Settings
- User profile
- API key management
- Usage statistics

## 🚀 Build for Production

```bash
npm run build
```

Output will be in `dist/` folder.

## 🌐 Deploy

### Vercel
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod
```

### Static Hosting
Upload `dist/` folder to any static hosting service.

---

**Built with ❤️ using React + Vite + TailwindCSS**
