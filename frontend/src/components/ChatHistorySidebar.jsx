import { useState, useEffect } from 'react';
import { MessageSquare, Plus, Trash2, Edit2, X, Check } from 'lucide-react';
import { conversationsAPI } from '../services/api';

export default function ChatHistorySidebar({ 
  currentConversationId, 
  onConversationSelect, 
  onNewConversation 
}) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoading(true);
      const response = await conversationsAPI.getAll({ limit: 50, active_only: true });
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const response = await conversationsAPI.create({
        title: 'محادثة جديدة'
      });
      setConversations([response.data, ...conversations]);
      onNewConversation(response.data.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      alert('فشل إنشاء المحادثة');
    }
  };

  const handleDeleteConversation = async (id, e) => {
    e.stopPropagation();
    
    if (!confirm('هل تريد حذف هذه المحادثة؟')) return;
    
    try {
      await conversationsAPI.delete(id);
      setConversations(conversations.filter(c => c.id !== id));
      
      // If deleting current conversation, create a new one
      if (id === currentConversationId) {
        handleCreateConversation();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('فشل حذف المحادثة');
    }
  };

  const handleStartEdit = (conversation, e) => {
    e.stopPropagation();
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleSaveEdit = async (id, e) => {
    e.stopPropagation();
    
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    
    try {
      const response = await conversationsAPI.update(id, { title: editTitle });
      setConversations(conversations.map(c => 
        c.id === id ? { ...c, title: response.data.title } : c
      ));
      setEditingId(null);
    } catch (error) {
      console.error('Failed to update conversation:', error);
      alert('فشل تحديث العنوان');
    }
  };

  const handleCancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditTitle('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'الآن';
    if (diffMins < 60) return `منذ ${diffMins} دقيقة`;
    if (diffHours < 24) return `منذ ${diffHours} ساعة`;
    if (diffDays === 1) return 'أمس';
    if (diffDays < 7) return `منذ ${diffDays} أيام`;
    
    return date.toLocaleDateString('ar-EG', { 
      day: 'numeric', 
      month: 'short' 
    });
  };

  return (
    <div className="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={handleCreateConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg font-medium"
        >
          <Plus className="h-5 w-5" />
          محادثة جديدة
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-8 px-4">
            <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">لا توجد محادثات</p>
            <p className="text-xs mt-1">ابدأ محادثة جديدة</p>
          </div>
        ) : (
          <div className="py-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className={`mx-2 mb-2 p-3 rounded-lg cursor-pointer transition-all group ${
                  conversation.id === currentConversationId
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 border-2 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    {editingId === conversation.id ? (
                      <div className="flex items-center gap-1">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          className="flex-1 px-2 py-1 text-sm border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveEdit(conversation.id, e);
                            if (e.key === 'Escape') handleCancelEdit(e);
                          }}
                        />
                        <button
                          onClick={(e) => handleSaveEdit(conversation.id, e)}
                          className="p-1 hover:bg-green-100 dark:hover:bg-green-900/20 rounded"
                        >
                          <Check className="h-4 w-4 text-green-600" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded"
                        >
                          <X className="h-4 w-4 text-red-600" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center gap-2">
                          <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
                          <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {conversation.title}
                          </h3>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {conversation.message_count} رسالة
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatDate(conversation.updated_at)}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                  
                  {editingId !== conversation.id && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleStartEdit(conversation, e)}
                        className="p-1 hover:bg-blue-100 dark:hover:bg-blue-900/20 rounded"
                        title="تعديل العنوان"
                      >
                        <Edit2 className="h-4 w-4 text-blue-600" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded"
                        title="حذف المحادثة"
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
