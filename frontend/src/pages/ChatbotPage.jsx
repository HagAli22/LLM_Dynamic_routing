import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, AlertCircle, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import { conversationsAPI, promptsAPI, feedbackAPI } from '../services/api';
import ChatHistorySidebar from '../components/ChatHistorySidebar';
import ModelRating from '../components/ModelRating';

export default function ChatbotPage({ user }) {
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load existing conversations or create new one
    loadOrCreateConversation();
  }, []);

  const loadOrCreateConversation = async () => {
    try {
      // First, try to get existing conversations
      const response = await conversationsAPI.getAll({ limit: 1, active_only: true });
      
      if (response.data && response.data.length > 0) {
        // Load the most recent conversation
        const latestConversation = response.data[0];
        await loadConversation(latestConversation.id);
      } else {
        // No conversations exist, create a new one
        await createInitialConversation();
      }
    } catch (error) {
      console.error('Failed to load or create conversation:', error);
      // Fallback: create new conversation
      await createInitialConversation();
    }
  };

  const createInitialConversation = async () => {
    try {
      const response = await conversationsAPI.create({
        title: 'New Conversation'
      });
      setCurrentConversationId(response.data.id);
    } catch (error) {
      console.error('Failed to create initial conversation:', error);
    }
  };

  const loadConversation = async (conversationId) => {
    try {
      setLoadingConversation(true);
      const response = await conversationsAPI.getById(conversationId);
      
      // Convert messages to the format expected by the component
      const formattedMessages = response.data.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        metadata: msg.message_metadata ? {
          ...msg.message_metadata,
          id: msg.query_id // Add query_id to metadata for feedback
        } : null
      }));
      
      setMessages(formattedMessages);
      setCurrentConversationId(conversationId);
    } catch (error) {
      console.error('Failed to load conversation:', error);
      alert('Failed to load conversation');
    } finally {
      setLoadingConversation(false);
    }
  };

  const handleNewConversation = (conversationId) => {
    setMessages([]);
    setCurrentConversationId(conversationId);
    setSuggestions(null);
  };

  const checkPromptClarity = async (prompt) => {
    try {
      const response = await promptsAPI.getSuggestions(prompt);
      if (!response.data.is_clear) {
        setSuggestions(response.data);
        return false;
      }
      return true;
    } catch (error) {
      return true;
    }
  };

  const handleSubmit = async (e, customPrompt = null) => {
    e?.preventDefault();
    const query = customPrompt || input;
    
    if (!query.trim() || !currentConversationId) return;

    // Check if prompt is clear
    if (!customPrompt) {
      const isPromptClear = await checkPromptClarity(query);
      if (!isPromptClear) {
        return;
      }
    }
    
    setSuggestions(null);
    setInput('');
    setLoading(true);

    // Add user message immediately
    const userMessage = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await conversationsAPI.sendMessage(currentConversationId, {
        query,
        skip_cache: false
      });
      
      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        metadata: {
          id: response.data.id,
          classification: response.data.classification,
          model_tier: response.data.model_tier,
          used_model: response.data.used_model,
          processing_time: response.data.processing_time,
          cache_hit: response.data.cache_hit,
        },
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'error',
        content: error.response?.data?.detail || 'An error occurred while processing the query',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (queryId, rating, messageIndex) => {
    try {
      await feedbackAPI.submit({
        query_id: queryId,
        rating: rating,
        response_helpful: rating === 'excellent' || rating === 'good',
      });
      
      // Update message to show feedback was submitted
      setMessages(prev => prev.map((msg, idx) => {
        if (idx === messageIndex && msg.metadata) {
          return {
            ...msg,
            metadata: {
              ...msg.metadata,
              user_rating: rating
            }
          };
        }
        return msg;
      }));
      
      // Show success notification based on rating
      const messages = {
        excellent: '⭐ Thanks! Your rating helps us improve the service',
        good: '👍 Thanks for your positive rating',
        poor: '🙏 Sorry for the bad experience, we will work on improvement'
      };
      
      // Create a temporary toast notification
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
      toast.textContent = messages[rating] || 'Thanks for your rating!';
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => document.body.removeChild(toast), 300);
      }, 3000);
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to send rating, try again');
    }
  };

  const useSuggestion = (suggestion) => {
    setInput(suggestion);
    setSuggestions(null);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]" dir="rtl">
      {/* Chat History Sidebar */}
      <ChatHistorySidebar
        currentConversationId={currentConversationId}
        onConversationSelect={loadConversation}
        onNewConversation={handleNewConversation}
      />
      
      {/* Main Chat Area */}
      <div className="flex-1 max-w-5xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl h-full flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-t-2xl">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <Sparkles className="ml-2 h-6 w-6 text-primary" />
            Smart Chatbot
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
            Ask any question and we'll choose the best LLM model to answer
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loadingConversation ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">Loading conversation...</p>
              </div>
            </div>
          ) : (
          <>
          {messages.length === 0 && (
            <div className="text-center text-gray-500 dark:text-gray-400 mt-20">
              <Sparkles className="h-16 w-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p className="text-lg">Start the conversation by asking your question</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                    : message.role === 'error'
                    ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                
                {message.metadata && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600 space-y-2">
                    <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-300">
                      <span className="flex items-center">
                        <span className="font-semibold ml-1">Classification:</span>
                        <span className={`px-2 py-1 rounded ${
                          message.metadata.classification === 'S' ? 'bg-green-100 text-green-800' :
                          message.metadata.classification === 'M' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {message.metadata.classification || 'N/A'}
                        </span>
                      </span>
                      {message.metadata.processing_time !== undefined && (
                        <span>{message.metadata.processing_time.toFixed(2)}s</span>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-300">
                        {message.metadata.cache_hit ? '💾 From Memory' : `🤖 ${message.metadata.used_model || 'N/A'}`}
                      </span>
                    </div>

                    {/* Model Rating Component */}
                    {message.metadata.id && message.metadata.used_model && (
                      <div className="pt-2">
                        <ModelRating
                          queryId={message.metadata.id}
                          modelIdentifier={message.metadata.used_model}
                          modelName={message.metadata.used_model?.split('/').pop()?.replace(':free', '') || 'Model'}
                          onRatingSuccess={(data) => {
                            console.log('Rating submitted:', data);
                            // You can update messages here if you want
                          }}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-end">
              <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-6 py-4">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
          </>
          )}
        </div>

        {/* Suggestions */}
        {suggestions && (
          <div className="mx-6 mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 ml-2 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                  {suggestions.explanation}
                </p>
                <div className="space-y-2">
                  {suggestions.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => useSuggestion(suggestion)}
                      className="block w-full text-right px-3 py-2 text-sm bg-white dark:bg-gray-700 hover:bg-yellow-100 dark:hover:bg-gray-600 border border-yellow-200 dark:border-yellow-700 rounded transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Write your question here..."
              className="flex-1 px-6 py-4 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white text-lg"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !currentConversationId}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg font-medium"
            >
              <Send className="h-6 w-6" />
            </button>
          </div>
        </form>
      </div>
    </div>
    </div>
  );
}
