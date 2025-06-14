import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Simple Student Setup Component
const StudentSetup = ({ onComplete }) => {
  const [formData, setFormData] = useState({
    name: '',
    grade_level: '9th',
    subjects: ['math'],
    learning_goals: [],
    study_hours_per_day: 2,
    preferred_study_time: 'evening'
  });

  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];
  const gradeOptions = ['6th', '7th', '8th', '9th', '10th', '11th', '12th'];

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

            <button
              type="submit"
              disabled={!formData.name}
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

// Simple Dashboard Component
const StudentDashboard = ({ student, onNavigate }) => {
  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome back, {student?.name || 'Student'}!</h1>
              <p className="text-gray-600">Grade {student?.grade_level} • Ready to learn!</p>
            </div>
          </div>
        </div>

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
      </div>
    </div>
  );
};

// Simple Chat Interface Component  
const ChatInterface = ({ student, subject, onNavigate }) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (student && subject) {
      createSession();
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
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
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
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

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('setup');
  const [currentSubject, setCurrentSubject] = useState(null);
  const [student, setStudent] = useState(null);

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
      setCurrentView('dashboard');
    } catch (error) {
      console.error('Error creating student:', error);
    }
  };

  if (currentView === 'setup') {
    return <StudentSetup onComplete={createStudent} />;
  }

  if (currentView === 'dashboard') {
    return <StudentDashboard student={student} onNavigate={navigate} />;
  }

  if (currentView === 'chat') {
    return <ChatInterface student={student} subject={currentSubject} onNavigate={navigate} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">🚧 Coming Soon!</h1>
        <p className="text-gray-600 mb-8">This feature is being built</p>
        <button
          onClick={() => navigate('dashboard')}
          className="bg-indigo-500 text-white px-6 py-3 rounded-lg hover:bg-indigo-600"
        >
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}

export default App;