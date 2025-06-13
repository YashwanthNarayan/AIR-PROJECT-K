import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Set up axios defaults for authentication
const setupAxiosAuth = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Login/Signup Component
const AuthPortal = ({ onAuthSuccess }) => {
  const [authMode, setAuthMode] = useState('select'); // 'select', 'student-login', 'student-signup', 'teacher-login', 'teacher-signup'
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    // Student specific
    grade_level: '9th',
    subjects: [],
    learning_goals: [],
    study_hours_per_day: 2,
    preferred_study_time: 'evening',
    // Teacher specific
    school_name: '',
    subjects_taught: [],
    grade_levels_taught: [],
    experience_years: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const subjects = ['math', 'physics', 'chemistry', 'biology', 'english', 'history', 'geography'];
  const gradeOptions = ['6th', '7th', '8th', '9th', '10th', '11th', '12th'];

  const handleSubjectToggle = (subject, isTeacher = false) => {
    const field = isTeacher ? 'subjects_taught' : 'subjects';
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(subject)
        ? prev[field].filter(s => s !== subject)
        : [...prev[field], subject]
    }));
  };

  const handleGradeLevelToggle = (grade) => {
    setFormData(prev => ({
      ...prev,
      grade_levels_taught: prev.grade_levels_taught.includes(grade)
        ? prev.grade_levels_taught.filter(g => g !== grade)
        : [...prev.grade_levels_taught, grade]
    }));
  };

  const handleLogin = async (userType) => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE}/api/auth/login`, {
        email: formData.email,
        password: formData.password,
        user_type: userType
      });
      
      const { access_token, user_type, user } = response.data;
      
      // Store token and user data
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_type', user_type);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Set up axios authentication
      setupAxiosAuth(access_token);
      
      onAuthSuccess(user_type, user);
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (userType) => {
    setIsLoading(true);
    setError('');
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    try {
      const endpoint = userType === 'student' 
        ? `${API_BASE}/api/auth/register/student`
        : `${API_BASE}/api/auth/register/teacher`;
      
      const payload = userType === 'student' 
        ? {
            name: formData.name,
            email: formData.email,
            password: formData.password,
            grade_level: formData.grade_level,
            subjects: formData.subjects,
            learning_goals: formData.learning_goals,
            study_hours_per_day: formData.study_hours_per_day,
            preferred_study_time: formData.preferred_study_time
          }
        : {
            name: formData.name,
            email: formData.email,
            password: formData.password,
            school_name: formData.school_name,
            subjects_taught: formData.subjects_taught,
            grade_levels_taught: formData.grade_levels_taught,
            experience_years: formData.experience_years
          };
      
      const response = await axios.post(endpoint, payload);
      const { access_token, user_type, user } = response.data;
      
      // Store token and user data
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_type', user_type);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Set up axios authentication
      setupAxiosAuth(access_token);
      
      onAuthSuccess(user_type, user);
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Portal Selection Screen
  if (authMode === 'select') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-6">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-12">
            <div className="w-20 h-20 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <span className="text-white font-bold text-3xl">K</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to Project K</h1>
            <p className="text-xl text-gray-600">Choose your portal to get started</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Student Portal */}
            <div className="bg-white rounded-3xl shadow-xl p-8 text-center transform hover:scale-105 transition-all duration-300">
              <div className="text-6xl mb-6">🎓</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Student Portal</h2>
              <p className="text-gray-600 mb-8">Access your personalized AI tutor, practice tests, and learning dashboard</p>
              <div className="space-y-3">
                <button
                  onClick={() => setAuthMode('student-login')}
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-3 px-6 rounded-xl font-medium hover:from-blue-600 hover:to-indigo-700 transition-all duration-200"
                >
                  Student Login
                </button>
                <button
                  onClick={() => setAuthMode('student-signup')}
                  className="w-full border-2 border-blue-500 text-blue-500 py-3 px-6 rounded-xl font-medium hover:bg-blue-50 transition-all duration-200"
                >
                  New Student? Sign Up
                </button>
              </div>
            </div>

            {/* Teacher Portal */}
            <div className="bg-white rounded-3xl shadow-xl p-8 text-center transform hover:scale-105 transition-all duration-300">
              <div className="text-6xl mb-6">👩‍🏫</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Teacher Portal</h2>
              <p className="text-gray-600 mb-8">Monitor student progress, manage classes, and access teaching insights</p>
              <div className="space-y-3">
                <button
                  onClick={() => setAuthMode('teacher-login')}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white py-3 px-6 rounded-xl font-medium hover:from-purple-600 hover:to-pink-700 transition-all duration-200"
                >
                  Teacher Login
                </button>
                <button
                  onClick={() => setAuthMode('teacher-signup')}
                  className="w-full border-2 border-purple-500 text-purple-500 py-3 px-6 rounded-xl font-medium hover:bg-purple-50 transition-all duration-200"
                >
                  New Teacher? Sign Up
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Login Forms
  if (authMode === 'student-login' || authMode === 'teacher-login') {
    const isStudent = authMode === 'student-login';
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <button
                onClick={() => setAuthMode('select')}
                className="text-gray-600 hover:text-gray-700 mb-4"
              >
                ← Back to portal selection
              </button>
              <div className="text-4xl mb-4">{isStudent ? '🎓' : '👩‍🏫'}</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {isStudent ? 'Student' : 'Teacher'} Login
              </h2>
              <p className="text-gray-600">Enter your credentials to continue</p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); handleLogin(isStudent ? 'student' : 'teacher'); }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`w-full mt-6 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  isStudent 
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700' 
                    : 'bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700'
                } text-white disabled:opacity-50`}
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>
            </form>

            <div className="text-center mt-6">
              <button
                onClick={() => setAuthMode(isStudent ? 'student-signup' : 'teacher-signup')}
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Don't have an account? Sign up
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Signup Forms
  if (authMode === 'student-signup' || authMode === 'teacher-signup') {
    const isStudent = authMode === 'student-signup';
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <button
                onClick={() => setAuthMode('select')}
                className="text-gray-600 hover:text-gray-700 mb-4"
              >
                ← Back to portal selection
              </button>
              <div className="text-4xl mb-4">{isStudent ? '🎓' : '👩‍🏫'}</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {isStudent ? 'Student' : 'Teacher'} Registration
              </h2>
              <p className="text-gray-600">Create your account to get started</p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); handleSignup(isStudent ? 'student' : 'teacher'); }}>
              <div className="space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
                    <input
                      type="password"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>
                </div>

                {/* Student-specific fields */}
                {isStudent && (
                  <>
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
                            <div className="text-xl mb-1">
                              {subject === 'math' && '🧮'}
                              {subject === 'physics' && '⚡'}
                              {subject === 'chemistry' && '🧪'}
                              {subject === 'biology' && '🧬'}
                              {subject === 'english' && '📖'}
                              {subject === 'history' && '🏛️'}
                              {subject === 'geography' && '🌍'}
                            </div>
                            <div className="capitalize text-sm font-medium">{subject}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {/* Teacher-specific fields */}
                {!isStudent && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">School Name</label>
                      <input
                        type="text"
                        value={formData.school_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, school_name: e.target.value }))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Subjects You Teach</label>
                      <div className="grid grid-cols-2 gap-3">
                        {subjects.map(subject => (
                          <button
                            key={subject}
                            type="button"
                            onClick={() => handleSubjectToggle(subject, true)}
                            className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                              formData.subjects_taught.includes(subject)
                                ? 'border-purple-500 bg-purple-50 text-purple-700'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <div className="text-xl mb-1">
                              {subject === 'math' && '🧮'}
                              {subject === 'physics' && '⚡'}
                              {subject === 'chemistry' && '🧪'}
                              {subject === 'biology' && '🧬'}
                              {subject === 'english' && '📖'}
                              {subject === 'history' && '🏛️'}
                              {subject === 'geography' && '🌍'}
                            </div>
                            <div className="capitalize text-sm font-medium">{subject}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Grade Levels You Teach</label>
                      <div className="grid grid-cols-4 gap-2">
                        {gradeOptions.map(grade => (
                          <button
                            key={grade}
                            type="button"
                            onClick={() => handleGradeLevelToggle(grade)}
                            className={`p-2 rounded-lg border-2 transition-all duration-200 text-sm ${
                              formData.grade_levels_taught.includes(grade)
                                ? 'border-purple-500 bg-purple-50 text-purple-700'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            {grade}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Teaching Experience (Years)</label>
                      <input
                        type="number"
                        min="0"
                        max="50"
                        value={formData.experience_years}
                        onChange={(e) => setFormData(prev => ({ ...prev, experience_years: parseInt(e.target.value) || 0 }))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading || (isStudent && formData.subjects.length === 0) || (!isStudent && (formData.subjects_taught.length === 0 || formData.grade_levels_taught.length === 0))}
                className={`w-full mt-8 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  isStudent 
                    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700' 
                    : 'bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700'
                } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isLoading ? 'Creating Account...' : `Create ${isStudent ? 'Student' : 'Teacher'} Account`}
              </button>
            </form>

            <div className="text-center mt-6">
              <button
                onClick={() => setAuthMode(isStudent ? 'student-login' : 'teacher-login')}
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Already have an account? Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

// Student Dashboard (Previous Implementation)
const StudentDashboard = ({ student, onNavigate, dashboardData, onLogout }) => {
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
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-indigo-600">{student?.total_xp || 0} XP</div>
                <div className="text-sm text-gray-600">🔥 {student?.streak_days || 0} day streak</div>
              </div>
              <button
                onClick={onLogout}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Logout
              </button>
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
      </div>
    </div>
  );
};

// Teacher Dashboard (New)
const TeacherDashboard = ({ teacher, onLogout }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Welcome, {teacher?.name || 'Teacher'}!</h1>
              <p className="text-gray-600">{teacher?.school_name} • {teacher?.experience_years} years experience</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-lg font-bold text-purple-600">{teacher?.students?.length || 0} Students</div>
                <div className="text-sm text-gray-600">👩‍🏫 {teacher?.subjects_taught?.length || 0} Subjects</div>
              </div>
              <button
                onClick={onLogout}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Coming Soon Message */}
        <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
          <div className="text-6xl mb-6">🚧</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Teacher Dashboard Coming Soon!</h2>
          <p className="text-xl text-gray-600 mb-8">
            We're building an amazing teacher experience with student analytics, class management, and progress tracking.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <div className="bg-purple-50 rounded-xl p-6">
              <div className="text-3xl mb-3">📊</div>
              <h3 className="font-semibold text-gray-900 mb-2">Student Analytics</h3>
              <p className="text-sm text-gray-600">Track individual student progress and learning patterns</p>
            </div>
            <div className="bg-pink-50 rounded-xl p-6">
              <div className="text-3xl mb-3">🏫</div>
              <h3 className="font-semibold text-gray-900 mb-2">Class Management</h3>
              <p className="text-sm text-gray-600">Organize students into classes and monitor group performance</p>
            </div>
            <div className="bg-indigo-50 rounded-xl p-6">
              <div className="text-3xl mb-3">💬</div>
              <h3 className="font-semibold text-gray-900 mb-2">Communication Tools</h3>
              <p className="text-sm text-gray-600">Send feedback and assignments to students</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Chat Interface (Updated with Auth)
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
      const response = await axios.post(`${API_BASE}/api/chat/session?subject=${subject}`);
      setSessionId(response.data.session_id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/chat/history?subject=${subject}`);
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
        user_message: message,
        subject: subject
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
          </div>
        </div>
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('auth'); // 'auth', 'student-dashboard', 'teacher-dashboard', 'chat', etc.
  const [currentSubject, setCurrentSubject] = useState(null);
  const [user, setUser] = useState(null);
  const [userType, setUserType] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  // Check for existing authentication on app load
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedUserType = localStorage.getItem('user_type');
    const storedUser = localStorage.getItem('user');

    if (token && storedUserType && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setupAxiosAuth(token);
        setUser(userData);
        setUserType(storedUserType);
        
        if (storedUserType === 'student') {
          setCurrentView('student-dashboard');
          loadDashboardData();
        } else {
          setCurrentView('teacher-dashboard');
        }
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        handleLogout();
      }
    }
  }, []);

  const navigate = (view, subject = null) => {
    setCurrentView(view);
    if (subject) {
      setCurrentSubject(subject);
    }
  };

  const handleAuthSuccess = (userType, userData) => {
    setUser(userData);
    setUserType(userType);
    
    if (userType === 'student') {
      setCurrentView('student-dashboard');
      loadDashboardData();
    } else {
      setCurrentView('teacher-dashboard');
    }
  };

  const loadDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user');
    setupAxiosAuth(null);
    setUser(null);
    setUserType(null);
    setCurrentView('auth');
    setDashboardData(null);
  };

  if (currentView === 'auth') {
    return <AuthPortal onAuthSuccess={handleAuthSuccess} />;
  }

  if (currentView === 'student-dashboard') {
    return <StudentDashboard student={user} onNavigate={navigate} dashboardData={dashboardData} onLogout={handleLogout} />;
  }

  if (currentView === 'teacher-dashboard') {
    return <TeacherDashboard teacher={user} onLogout={handleLogout} />;
  }

  if (currentView === 'chat') {
    return <ChatInterface student={user} subject={currentSubject} onNavigate={navigate} />;
  }

  // Other views can be added here (mindfulness, practice, progress, etc.)
  return <div>Feature coming soon!</div>;
}

export default App;