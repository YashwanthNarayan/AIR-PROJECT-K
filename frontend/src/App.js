import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [welcomeData, setWelcomeData] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Create session on component mount
    createSession();
  }, []);

  const createSession = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/chat/session`, {
        student_name: studentName || 'Student'
      });
      setSessionId(response.data.session_id);
      
      // Get welcome message
      const welcomeResponse = await axios.get(`${API_BASE}/api/welcome/${response.data.session_id}`);
      setWelcomeData(welcomeResponse.data);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const sendMessage = async (message = inputMessage) => {
    if (!message.trim() || !sessionId || isLoading) return;

    const userMessage = { 
      text: message, 
      sender: 'user', 
      timestamp: new Date().toLocaleTimeString() 
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/api/chat/message`, {
        session_id: sessionId,
        user_message: message
      });

      const botMessage = {
        text: response.data.bot_response,
        sender: 'bot',
        bot_type: response.data.bot_type,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        text: "Sorry, I'm having trouble connecting right now. Please try again!",
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'math_help':
        sendMessage("I need help with math");
        break;
      case 'study_now':
        sendMessage("I want to start studying");
        break;
      case 'review':
        sendMessage("Can you help me review what I've learned?");
        break;
      case 'quiz':
        sendMessage("I'd like to take a practice quiz");
        break;
      default:
        sendMessage(action);
    }
  };

  const getBotIcon = (botType) => {
    switch (botType) {
      case 'math_bot':
        return '🧮';
      case 'central_brain':
        return '🧠';
      default:
        return '🤖';
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-indigo-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">K</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Project K</h1>
                <p className="text-sm text-gray-600">Your AI Learning Companion</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden sm:flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm text-gray-600">Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        {welcomeData && messages.length === 0 && (
          <div className="mb-8 text-center">
            <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                {welcomeData.message}
              </h2>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                {welcomeData.quick_actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action.action)}
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-3 rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 font-medium"
                  >
                    {action.text}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat Container */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          {/* Messages */}
          <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <div className="text-6xl mb-4">🎓</div>
                <p className="text-lg">Ready to start learning? Ask me anything!</p>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                    message.sender === 'user'
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                      : message.error
                      ? 'bg-red-100 text-red-800 border border-red-200'
                      : 'bg-white text-gray-800 shadow-md border border-gray-200'
                  }`}
                >
                  {message.sender === 'bot' && (
                    <div className="flex items-center mb-2">
                      <span className="text-lg mr-2">{getBotIcon(message.bot_type)}</span>
                      <span className="text-xs font-medium text-gray-600">
                        {message.bot_type === 'math_bot' ? 'Math Tutor' : 'AI Tutor'}
                      </span>
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  <div className={`text-xs mt-2 ${
                    message.sender === 'user' ? 'text-indigo-100' : 'text-gray-500'
                  }`}>
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white text-gray-800 shadow-md border border-gray-200 px-4 py-3 rounded-2xl">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    <span className="text-sm text-gray-600 ml-2">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-6 bg-white border-t border-gray-200">
            <div className="flex space-x-4">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about math, or just say hello..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={isLoading || !sessionId}
              />
              <button
                onClick={() => sendMessage()}
                disabled={isLoading || !sessionId || !inputMessage.trim()}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
            <div className="mt-3 text-xs text-gray-500 text-center">
              💡 Tip: I use the Socratic method - I'll guide you to the answer rather than just giving it to you!
            </div>
          </div>
        </div>

        {/* Features Preview */}
        {messages.length === 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-md">
              <div className="text-3xl mb-3">🧮</div>
              <h3 className="font-semibold text-gray-900 mb-2">Math Tutoring</h3>
              <p className="text-sm text-gray-600">Get help with algebra, geometry, calculus and more using proven teaching methods.</p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-md">
              <div className="text-3xl mb-3">🧠</div>
              <h3 className="font-semibold text-gray-900 mb-2">Smart Learning</h3>
              <p className="text-sm text-gray-600">AI adapts to your learning style and guides you through problems step by step.</p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-md">
              <div className="text-3xl mb-3">📚</div>
              <h3 className="font-semibold text-gray-900 mb-2">24/7 Available</h3>
              <p className="text-sm text-gray-600">Get homework help anytime, anywhere. Your personal tutor never sleeps!</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;