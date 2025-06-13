import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Student Setup Component
const StudentSetup = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    name: '',
    grade_level: '9th',
    subjects: [],
    learning_goals: [],
    study_hours_per_day: 2,
    preferred_study_time: 'evening'
  });

  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];
  const gradeOptions = ['6th', '7th', '8th', '9th', '10th', '11th', '12th'];

  const handleSubjectToggle = (subject) => {
    setFormData(prev => ({
      ...prev,
      subjects: prev.subjects.includes(subject)
        ? prev.subjects.filter(s => s !== subject)
        : [...prev.subjects, subject]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onComplete(formData);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-2xl">K</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to Project K!</h1>
            <p className="text-gray-600">Let's set up your personalized learning profile</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Your Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Grade Level</label>
              <select
                value={formData.grade_level}
                onChange={(e) => setFormData(prev => ({ ...prev, grade_level: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {gradeOptions.map(grade => (
                  <option key={grade} value={grade}>{grade} Grade</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subjects to Study</label>
              <div className="grid grid-cols-2 gap-3">
                {subjects.map(subject => (
                  <button
                    key={subject}
                    type="button"
                    onClick={() => handleSubjectToggle(subject)}
                    className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                      formData.subjects.includes(subject)
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">
                      {subject === 'math' && '🧮'}
                      {subject === 'physics' && '⚡'}
                      {subject === 'chemistry' && '🧪'}
                      {subject === 'biology' && '🧬'}
                      {subject === 'english' && '📖'}
                      {subject === 'history' && '🏛️'}
                      {subject === 'geography' && '🌍'}
                    </div>
                    <div className="capitalize font-medium">{subject}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Daily Study Hours</label>
              <select
                value={formData.study_hours_per_day}
                onChange={(e) => setFormData(prev => ({ ...prev, study_hours_per_day: parseInt(e.target.value) }))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value={1}>1 hour</option>
                <option value={2}>2 hours</option>
                <option value={3}>3 hours</option>
                <option value={4}>4+ hours</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={!formData.name || formData.subjects.length === 0}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-4 px-6 rounded-lg font-medium hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              Start Learning Journey! 🚀
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

// Student Dashboard Component
const StudentDashboard = ({ student, onNavigate, dashboardData }) => {
  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome back, {student?.name || 'Student'}!</h1>
              <p className="text-gray-600">Grade {student?.grade_level} • Level {student?.level || 1}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-indigo-600">{student?.total_xp || 0} XP</div>
              <div className="text-sm text-gray-600">🔥 {student?.streak_days || 0} day streak</div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">📚</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.subjects_studied || 0}</div>
                <div className="text-sm text-gray-600">Subjects Studied</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">💬</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.total_messages || 0}</div>
                <div className="text-sm text-gray-600">Questions Asked</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">🏆</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{student?.level || 1}</div>
                <div className="text-sm text-gray-600">Current Level</div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">🔥</span>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{student?.streak_days || 0}</div>
                <div className="text-sm text-gray-600">Day Streak</div>
              </div>
            </div>
          </div>
        </div>

        {/* Subjects Grid */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Choose a Subject to Study</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {subjects.map((subject) => (
              <button
                key={subject}
                onClick={() => onNavigate('chat', subject)}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-6 rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 text-center"
              >
                <div className="text-3xl mb-2">
                  {subject === 'math' && '🧮'}
                  {subject === 'physics' && '⚡'}
                  {subject === 'chemistry' && '🧪'}
                  {subject === 'biology' && '🧬'}
                  {subject === 'english' && '📖'}
                  {subject === 'history' && '🏛️'}
                  {subject === 'geography' && '🌍'}
                </div>
                <div className="font-medium capitalize">{subject}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <button
            onClick={() => onNavigate('practice')}
            className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="text-3xl mb-3">📝</div>
            <h3 className="font-semibold text-gray-900 mb-2">Practice Tests</h3>
            <p className="text-sm text-gray-600">Take adaptive quizzes to test your knowledge</p>
          </button>
          <button
            onClick={() => onNavigate('mindfulness')}
            className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="text-3xl mb-3">🧘</div>
            <h3 className="font-semibold text-gray-900 mb-2">Mindfulness</h3>
            <p className="text-sm text-gray-600">Breathing exercises and stress management</p>
          </button>
          <button
            onClick={() => onNavigate('progress')}
            className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all duration-200 text-left"
          >
            <div className="text-3xl mb-3">📊</div>
            <h3 className="font-semibold text-gray-900 mb-2">Progress Tracker</h3>
            <p className="text-sm text-gray-600">View your learning progress and achievements</p>
          </button>
        </div>

        {/* Recent Activity */}
        {dashboardData?.recent_activity?.messages?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {dashboardData.recent_activity.messages.slice(0, 5).map((message, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl">
                    {message.subject === 'math' && '🧮'}
                    {message.subject === 'physics' && '⚡'}
                    {message.subject === 'chemistry' && '🧪'}
                    {message.subject === 'biology' && '🧬'}
                    {message.subject === 'english' && '📖'}
                    {message.subject === 'history' && '🏛️'}
                    {message.subject === 'geography' && '🌍'}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium capitalize">{message.subject}</div>
                    <div className="text-sm text-gray-600 truncate">{message.user_message}</div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(message.timestamp).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Chat Interface Component
const ChatInterface = ({ student, subject, onNavigate }) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (student && subject) {
      createSession();
      loadChatHistory();
    }
  }, [student, subject]);

  const createSession = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/chat/session`, {
        student_id: student.student_id,
        subject: subject
      });
      setSessionId(response.data.session_id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/chat/history/${student.student_id}?subject=${subject}`);
      const history = [];
      response.data.forEach(msg => {
        history.push({
          text: msg.user_message,
          sender: 'user',
          timestamp: new Date(msg.timestamp).toLocaleTimeString()
        });
        history.push({
          text: msg.bot_response,
          sender: 'bot',
          bot_type: msg.bot_type,
          timestamp: new Date(msg.timestamp).toLocaleTimeString()
        });
      });
      setMessages(history);
    } catch (error) {
      console.error('Error loading chat history:', error);
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
        student_id: student.student_id,
        subject: subject,
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

  const getBotIcon = (botType) => {
    if (botType?.includes('math')) return '🧮';
    if (botType?.includes('physics')) return '⚡';
    if (botType?.includes('chemistry')) return '🧪';
    if (botType?.includes('biology')) return '🧬';
    if (botType?.includes('english')) return '📖';
    if (botType?.includes('history')) return '🏛️';
    if (botType?.includes('geography')) return '🌍';
    if (botType?.includes('mindfulness')) return '🧘';
    return '🧠';
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
              <button
                onClick={() => onNavigate('dashboard')}
                className="text-indigo-600 hover:text-indigo-700"
              >
                ← Back
              </button>
              <div className="text-2xl">
                {subject === 'math' && '🧮'}
                {subject === 'physics' && '⚡'}
                {subject === 'chemistry' && '🧪'}
                {subject === 'biology' && '🧬'}
                {subject === 'english' && '📖'}
                {subject === 'history' && '🏛️'}
                {subject === 'geography' && '🌍'}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 capitalize">{subject} Tutor</h1>
                <p className="text-sm text-gray-600">Personalized learning with AI</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Chat Container */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          {/* Messages */}
          <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <div className="text-6xl mb-4">
                  {subject === 'math' && '🧮'}
                  {subject === 'physics' && '⚡'}
                  {subject === 'chemistry' && '🧪'}
                  {subject === 'biology' && '🧬'}
                  {subject === 'english' && '📖'}
                  {subject === 'history' && '🏛️'}
                  {subject === 'geography' && '🌍'}
                </div>
                <p className="text-lg">Ready to learn {subject}? Ask me anything!</p>
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
                        {message.bot_type?.includes('mindfulness') ? 'Mindfulness Guide' 
                         : message.bot_type?.includes('central') ? 'AI Tutor'
                         : `${subject?.charAt(0).toUpperCase() + subject?.slice(1)} Tutor`}
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
                placeholder={`Ask me anything about ${subject}...`}
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
              💡 I use the Socratic method - I'll guide you to the answer rather than just giving it to you!
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// Mindfulness Component
const MindfulnessComponent = ({ student, onNavigate }) => {
  const [currentActivity, setCurrentActivity] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [timer, setTimer] = useState(0);

  const activities = [
    { id: 'breathing', name: 'Breathing Exercise', icon: '🫁', duration: 5, description: '4-7-8 breathing technique' },
    { id: 'meditation', name: 'Quick Meditation', icon: '🧘', duration: 3, description: 'Short guided meditation' },
    { id: 'stress', name: 'Stress Relief', icon: '😌', duration: 2, description: 'Quick stress reduction' },
    { id: 'break', name: 'Study Break', icon: '☕', duration: 5, description: 'Refreshing break activities' }
  ];

  const startActivity = (activity) => {
    setCurrentActivity(activity);
    setIsActive(true);
    setTimer(activity.duration * 60);
  };

  const stopActivity = () => {
    setIsActive(false);
    setCurrentActivity(null);
    setTimer(0);
  };

  useEffect(() => {
    let interval = null;
    if (isActive && timer > 0) {
      interval = setInterval(() => {
        setTimer(timer => timer - 1);
      }, 1000);
    } else if (timer === 0 && isActive) {
      setIsActive(false);
    }
    return () => clearInterval(interval);
  }, [isActive, timer]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button
            onClick={() => onNavigate('dashboard')}
            className="text-indigo-600 hover:text-indigo-700 mr-4"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🧘 Mindfulness Toolbox</h1>
            <p className="text-gray-600">Take care of your mental well-being</p>
          </div>
        </div>

        {!currentActivity ? (
          /* Activity Selection */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {activities.map((activity) => (
              <button
                key={activity.id}
                onClick={() => startActivity(activity)}
                className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 text-left"
              >
                <div className="text-6xl mb-4">{activity.icon}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{activity.name}</h3>
                <p className="text-gray-600 mb-4">{activity.description}</p>
                <div className="text-sm text-indigo-600 font-medium">{activity.duration} minutes</div>
              </button>
            ))}
          </div>
        ) : (
          /* Active Session */
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="text-8xl mb-6">{currentActivity.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{currentActivity.name}</h2>
            <div className="text-6xl font-bold text-indigo-600 mb-6">{formatTime(timer)}</div>
            
            {currentActivity.id === 'breathing' && (
              <div className="mb-6">
                <p className="text-lg text-gray-700 mb-4">Follow the breathing pattern:</p>
                <div className="space-y-2">
                  <div>Inhale for 4 seconds</div>
                  <div>Hold for 7 seconds</div>
                  <div>Exhale for 8 seconds</div>
                </div>
              </div>
            )}

            {currentActivity.id === 'meditation' && (
              <div className="mb-6">
                <p className="text-lg text-gray-700 mb-4">Close your eyes and focus on your breath.</p>
                <p className="text-gray-600">Let thoughts come and go without judgment.</p>
              </div>
            )}

            <button
              onClick={stopActivity}
              className="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors"
            >
              Stop Session
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Practice Test Component
const PracticeTestComponent = ({ student, onNavigate }) => {
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentQuestions, setCurrentQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const subjects = {
    math: { name: 'Mathematics', topics: ['Algebra', 'Geometry', 'Calculus', 'Statistics'] },
    physics: { name: 'Physics', topics: ['Mechanics', 'Thermodynamics', 'Optics', 'Electricity'] },
    chemistry: { name: 'Chemistry', topics: ['Atomic Structure', 'Organic Chemistry', 'Acids & Bases'] },
    biology: { name: 'Biology', topics: ['Cell Biology', 'Genetics', 'Ecology', 'Human Physiology'] }
  };

  const sampleQuestions = {
    math: [
      {
        id: '1',
        question: 'Solve for x: 2x + 5 = 15',
        options: ['x = 5', 'x = 10', 'x = 7.5', 'x = 2.5'],
        correctAnswer: 'x = 5',
        explanation: 'Subtract 5 from both sides: 2x = 10. Then divide by 2: x = 5.'
      },
      {
        id: '2',
        question: 'What is the area of a circle with radius 3?',
        options: ['9π', '6π', '3π', '12π'],
        correctAnswer: '9π',
        explanation: 'Area = πr². With r = 3, Area = π(3)² = 9π.'
      }
    ],
    physics: [
      {
        id: '1',
        question: 'What is Newton\'s First Law of Motion?',
        options: ['F = ma', 'An object at rest stays at rest unless acted upon by a force', 'For every action there is an equal and opposite reaction', 'None of the above'],
        correctAnswer: 'An object at rest stays at rest unless acted upon by a force',
        explanation: 'Newton\'s First Law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force.'
      }
    ]
  };

  const generatePracticeTest = () => {
    setIsGenerating(true);
    // Simulate API call
    setTimeout(() => {
      const questions = sampleQuestions[selectedSubject] || [];
      setCurrentQuestions(questions);
      setCurrentQuestionIndex(0);
      setUserAnswers({});
      setShowResults(false);
      setIsGenerating(false);
    }, 1000);
  };

  const handleAnswerSelect = (questionId, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < currentQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const calculateScore = () => {
    let correct = 0;
    currentQuestions.forEach(q => {
      if (userAnswers[q.id] === q.correctAnswer) {
        correct++;
      }
    });
    return (correct / currentQuestions.length) * 100;
  };

  if (showResults) {
    const score = calculateScore();
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="text-6xl mb-6">🎉</div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Test Complete!</h2>
            <div className="text-4xl font-bold text-indigo-600 mb-6">{score.toFixed(0)}%</div>
            <p className="text-lg text-gray-700 mb-8">
              You scored {Math.round((score/100) * currentQuestions.length)} out of {currentQuestions.length} questions correctly!
            </p>
            <div className="space-x-4">
              <button
                onClick={() => setCurrentQuestions([])}
                className="bg-indigo-500 text-white px-6 py-3 rounded-lg hover:bg-indigo-600"
              >
                Take Another Test
              </button>
              <button
                onClick={() => onNavigate('dashboard')}
                className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (currentQuestions.length > 0) {
    const currentQuestion = currentQuestions[currentQuestionIndex];
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Practice Test</h2>
              <div className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {currentQuestions.length}
              </div>
            </div>
            
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">{currentQuestion.question}</h3>
              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => handleAnswerSelect(currentQuestion.id, option)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                      userAnswers[currentQuestion.id] === option
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={nextQuestion}
              disabled={!userAnswers[currentQuestion.id]}
              className="w-full bg-indigo-500 text-white py-3 rounded-lg hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentQuestionIndex === currentQuestions.length - 1 ? 'Finish Test' : 'Next Question'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center mb-8">
          <button
            onClick={() => onNavigate('dashboard')}
            className="text-indigo-600 hover:text-indigo-700 mr-4"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📝 Practice Tests</h1>
            <p className="text-gray-600">Test your knowledge with adaptive quizzes</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Choose a subject</option>
                {Object.entries(subjects).map(([key, subject]) => (
                  <option key={key} value={key}>{subject.name}</option>
                ))}
              </select>
            </div>

            {selectedSubject && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Topic</label>
                <select
                  value={selectedTopic}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Choose a topic</option>
                  {subjects[selectedSubject].topics.map((topic) => (
                    <option key={topic} value={topic}>{topic}</option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <button
              onClick={generatePracticeTest}
              disabled={!selectedSubject || !selectedTopic || isGenerating}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-4 px-6 rounded-lg font-medium hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating Test...' : 'Start Practice Test'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Progress Tracker Component
const ProgressTracker = ({ student, onNavigate }) => {
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    if (student) {
      loadDashboardData();
    }
  }, [student]);

  const loadDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/dashboard/${student.student_id}`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  };

  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];
  
  const getSubjectProgress = (subject) => {
    // Simulate progress calculation
    const baseProgress = (student?.level || 1) * 10;
    const randomVariation = Math.random() * 40;
    return Math.min(100, baseProgress + randomVariation);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center mb-8">
          <button
            onClick={() => onNavigate('dashboard')}
            className="text-indigo-600 hover:text-indigo-700 mr-4"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📊 Progress Tracker</h1>
            <p className="text-gray-600">Track your learning journey and achievements</p>
          </div>
        </div>

        {/* Overall Progress */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Overall Progress</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-indigo-600 mb-2">{student?.level || 1}</div>
              <div className="text-gray-600">Current Level</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">{student?.total_xp || 0}</div>
              <div className="text-gray-600">Total XP</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-orange-600 mb-2">{student?.streak_days || 0}</div>
              <div className="text-gray-600">Day Streak</div>
            </div>
          </div>
        </div>

        {/* Subject Progress */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Subject Mastery</h2>
          <div className="space-y-4">
            {subjects.map((subject) => {
              const progress = getSubjectProgress(subject);
              return (
                <div key={subject} className="flex items-center space-x-4">
                  <div className="w-12 text-2xl">
                    {subject === 'math' && '🧮'}
                    {subject === 'physics' && '⚡'}
                    {subject === 'chemistry' && '🧪'}
                    {subject === 'biology' && '🧬'}
                    {subject === 'english' && '📖'}
                    {subject === 'history' && '🏛️'}
                    {subject === 'geography' && '🌍'}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium capitalize">{subject}</span>
                      <span className="text-sm text-gray-600">{progress.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Achievements */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Achievements</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl mb-2">🥇</div>
              <div className="font-medium">First Question</div>
              <div className="text-sm text-gray-600">Asked your first question</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl mb-2">🔥</div>
              <div className="font-medium">Study Streak</div>
              <div className="text-sm text-gray-600">3 days in a row</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl mb-2">🧮</div>
              <div className="font-medium">Math Explorer</div>
              <div className="text-sm text-gray-600">Studied math topics</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl mb-2">🧘</div>
              <div className="font-medium">Mindful Learner</div>
              <div className="text-sm text-gray-600">Used mindfulness tools</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('setup');
  const [currentSubject, setCurrentSubject] = useState(null);
  const [student, setStudent] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  const navigate = (view, subject = null) => {
    setCurrentView(view);
    if (subject) {
      setCurrentSubject(subject);
    }
  };

  const createStudent = async (studentData) => {
    try {
      const response = await axios.post(`${API_BASE}/api/student/profile`, studentData);
      setStudent(response.data);
      await loadDashboardData(response.data.student_id);
      setCurrentView('dashboard');
    } catch (error) {
      console.error('Error creating student:', error);
    }
  };

  const loadDashboardData = async (studentId) => {
    try {
      const response = await axios.get(`${API_BASE}/api/dashboard/${studentId}`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  if (currentView === 'setup') {
    return <StudentSetup onComplete={createStudent} />;
  }

  if (currentView === 'dashboard') {
    return <StudentDashboard student={student} onNavigate={navigate} dashboardData={dashboardData} />;
  }

  if (currentView === 'chat') {
    return <ChatInterface student={student} subject={currentSubject} onNavigate={navigate} />;
  }

  if (currentView === 'mindfulness') {
    return <MindfulnessComponent student={student} onNavigate={navigate} />;
  }

  if (currentView === 'practice') {
    return <PracticeTestComponent student={student} onNavigate={navigate} />;
  }

  if (currentView === 'progress') {
    return <ProgressTracker student={student} onNavigate={navigate} />;
  }

  return <div>Feature coming soon!</div>;
}

export default App;