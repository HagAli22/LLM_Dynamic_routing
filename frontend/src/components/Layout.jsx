import { Outlet, Link, useLocation } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, FileStack, Settings, LogOut, Zap } from 'lucide-react';

export default function Layout({ user, onLogout }) {
  const location = useLocation();

  const navigation = [
    { name: 'Chatbot', href: '/chatbot', icon: MessageSquare },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Batch Processing', href: '/batch', icon: FileStack },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900" dir="rtl">
      {/* Sidebar */}
      <aside className="fixed top-0 right-0 z-40 w-64 h-screen bg-white dark:bg-gray-800 shadow-lg border-l border-gray-200 dark:border-gray-700">
        <div className="h-full px-3 py-4 overflow-y-auto">
          {/* Logo */}
          <div className="flex items-center mb-8 px-3">
            <Zap className="h-8 w-8 text-primary ml-2" />
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              LLM Router
            </h1>
          </div>

          {/* User Info */}
          <div className="mb-6 p-3 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-lg">
            <p className="text-sm font-medium text-gray-900 dark:text-white">{user.username}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
            <div className="mt-2 text-xs">
              <span className="text-gray-600 dark:text-gray-300">
                {user.queries_used_this_month} / {user.monthly_query_limit} استعلامات
              </span>
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mt-1">
                <div
                  className="bg-blue-600 h-1.5 rounded-full"
                  style={{ width: `${(user.queries_used_this_month / user.monthly_query_limit) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-primary text-white shadow-lg shadow-primary/30'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="h-5 w-5 ml-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            className="flex items-center w-full px-3 py-2.5 mt-auto text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors absolute bottom-4"
          >
            <LogOut className="h-5 w-5 ml-3" />
            تسجيل الخروج
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="mr-64 p-8">
        <Outlet />
      </main>
    </div>
  );
}
