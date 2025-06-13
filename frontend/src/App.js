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

// Teacher Dashboard (Complete V3)
const TeacherDashboard = ({ teacher, onLogout }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedView, setSelectedView] = useState('overview'); // 'overview', 'students', 'classes', 'analytics', 'assignments'
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentAnalytics, setStudentAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/teacher/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading teacher dashboard:', error);
    }
  };

  const loadStudentAnalytics = async (studentId) => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/teacher/student/${studentId}/analytics`);
      setStudentAnalytics(response.data);
      setSelectedStudent(studentId);
    } catch (error) {
      console.error('Error loading student analytics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Overview Tab
  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-md">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">👥</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.total_students || 0}</div>
              <div className="text-sm text-gray-600">Total Students</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-md">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">🏫</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.total_classes || 0}</div>
              <div className="text-sm text-gray-600">Classes</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-md">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">🚨</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.active_alerts || 0}</div>
              <div className="text-sm text-gray-600">Active Alerts</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-md">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">📚</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{dashboardData?.stats?.subjects_taught?.length || 0}</div>
              <div className="text-sm text-gray-600">Subjects</div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Recent Student Activity</h3>
        <div className="space-y-3">
          {dashboardData?.recent_activity?.slice(0, 8).map((activity, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl">
                {activity.subject === 'math' && '🧮'}
                {activity.subject === 'physics' && '⚡'}
                {activity.subject === 'chemistry' && '🧪'}
                {activity.subject === 'biology' && '🧬'}
                {activity.subject === 'english' && '📖'}
                {activity.subject === 'history' && '🏛️'}
                {activity.subject === 'geography' && '🌍'}
              </div>
              <div className="flex-1">
                <div className="font-medium">{activity.student_name}</div>
                <div className="text-sm text-gray-600 capitalize">{activity.subject}: {activity.message_preview}</div>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(activity.timestamp).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      {dashboardData?.alerts?.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Active Alerts</h3>
          <div className="space-y-3">
            {dashboardData.alerts.map((alert, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="text-2xl">🚨</div>
                <div className="flex-1">
                  <div className="font-medium text-red-800">{alert.title}</div>
                  <div className="text-sm text-red-600">{alert.description}</div>
                </div>
                <div className="text-xs text-red-500">
                  {new Date(alert.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Students Tab
  const StudentsTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-900">My Students</h3>
        <button
          onClick={() => setSelectedView('add-students')}
          className="bg-indigo-500 text-white px-4 py-2 rounded-lg hover:bg-indigo-600"
        >
          Add Students
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dashboardData?.students?.map((student) => (
          <div key={student.student_id} className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">{student.name.charAt(0)}</span>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">{student.name}</h4>
                <p className="text-sm text-gray-600">Grade {student.grade_level}</p>
              </div>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">XP:</span>
                <span className="font-medium">{student.total_xp || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Level:</span>
                <span className="font-medium">{student.level || 1}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Streak:</span>
                <span className="font-medium">{student.streak_days || 0} days</span>
              </div>
            </div>

            <button
              onClick={() => loadStudentAnalytics(student.student_id)}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-2 px-4 rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all"
            >
              View Analytics
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  // Student Analytics Modal
  const StudentAnalyticsModal = () => {
    if (!studentAnalytics) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50">
        <div className="bg-white rounded-2xl max-w-4xl w-full max-h-screen overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Student Analytics: {studentAnalytics.student_name}
              </h2>
              <button
                onClick={() => {setStudentAnalytics(null); setSelectedStudent(null);}}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {/* Student Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">{studentAnalytics.total_xp}</div>
                <div className="text-sm text-blue-800">Total XP</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{studentAnalytics.level}</div>
                <div className="text-sm text-green-800">Current Level</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">{studentAnalytics.total_messages}</div>
                <div className="text-sm text-purple-800">Messages</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-600">{studentAnalytics.streak_days}</div>
                <div className="text-sm text-orange-800">Day Streak</div>
              </div>
            </div>

            {/* Subject Activity */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Subject Activity</h3>
              <div className="space-y-3">
                {Object.entries(studentAnalytics.subjects_activity || {}).map(([subject, activity]) => (
                  <div key={subject} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">
                        {subject === 'math' && '🧮'}
                        {subject === 'physics' && '⚡'}
                        {subject === 'chemistry' && '🧪'}
                        {subject === 'biology' && '🧬'}
                        {subject === 'english' && '📖'}
                        {subject === 'history' && '🏛️'}
                        {subject === 'geography' && '🌍'}
                      </span>
                      <span className="font-medium capitalize">{subject}</span>
                    </div>
                    <div className="text-sm text-gray-600">{activity.count} messages</div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Insights */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Insights</h3>
              <div className="bg-indigo-50 p-4 rounded-lg">
                <p className="text-indigo-800 whitespace-pre-wrap">{studentAnalytics.ai_insights}</p>
              </div>
            </div>

            {/* Struggling Subjects */}
            {studentAnalytics.struggling_subjects?.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Needs Attention</h3>
                <div className="flex flex-wrap gap-2">
                  {studentAnalytics.struggling_subjects.map((subject) => (
                    <span
                      key={subject}
                      className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium"
                    >
                      {subject}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {studentAnalytics.recommended_actions?.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Classes Tab
  const ClassesTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-900">My Classes</h3>
        <button
          onClick={() => setSelectedView('create-class')}
          className="bg-indigo-500 text-white px-4 py-2 rounded-lg hover:bg-indigo-600"
        >
          Create Class
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dashboardData?.classes?.map((classroom) => (
          <div key={classroom.class_id} className="bg-white rounded-xl p-6 shadow-md">
            <div className="mb-4">
              <h4 className="font-semibold text-gray-900 text-lg">{classroom.name}</h4>
              <p className="text-sm text-gray-600 capitalize">
                {classroom.subject} • Grade {classroom.grade_level}
              </p>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Students:</span>
                <span className="font-medium">{classroom.students?.length || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Created:</span>
                <span className="font-medium">{new Date(classroom.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            <button className="w-full bg-indigo-500 text-white py-2 px-4 rounded-lg hover:bg-indigo-600 transition-colors">
              Manage Class
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h1>
              <p className="text-gray-600">{teacher?.name} • {teacher?.school_name}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-lg font-bold text-purple-600">{dashboardData?.stats?.total_students || 0} Students</div>
                <div className="text-sm text-gray-600">📚 {dashboardData?.stats?.subjects_taught?.length || 0} Subjects</div>
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

        {/* Navigation Tabs */}
        <div className="bg-white rounded-2xl shadow-lg mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { key: 'overview', label: 'Overview', icon: '📊' },
                { key: 'students', label: 'Students', icon: '👥' },
                { key: 'classes', label: 'Classes', icon: '🏫' },
                { key: 'analytics', label: 'Analytics', icon: '📈' },
                { key: 'assignments', label: 'Assignments', icon: '📋' }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setSelectedView(tab.key)}
                  className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                    selectedView === tab.key
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content Area */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          {selectedView === 'overview' && <OverviewTab />}
          {selectedView === 'students' && <StudentsTab />}
          {selectedView === 'classes' && <ClassesTab />}
          {selectedView === 'analytics' && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📈</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Advanced Analytics</h3>
              <p className="text-gray-600">Comprehensive student performance analytics coming soon!</p>
            </div>
          )}
          {selectedView === 'assignments' && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Assignment Manager</h3>
              <p className="text-gray-600">Create and manage student assignments coming soon!</p>
            </div>
          )}
        </div>

        {/* Loading Overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-40">
            <div className="bg-white rounded-lg p-6">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                <span>Loading analytics...</span>
              </div>
            </div>
          </div>
        )}

        {/* Student Analytics Modal */}
        {studentAnalytics && <StudentAnalyticsModal />}
      </div>
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
            onClick={() => onNavigate('student-dashboard')}
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
                onClick={() => onNavigate('student-dashboard')}
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
            onClick={() => onNavigate('student-dashboard')}
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
      const response = await axios.get(`${API_BASE}/api/dashboard`);
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
            onClick={() => onNavigate('student-dashboard')}
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
              <div className="text-sm text-gray-600">{student?.streak_days || 0} days in a row</div>
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

  if (currentView === 'mindfulness') {
    return <MindfulnessComponent student={user} onNavigate={navigate} />;
  }

  if (currentView === 'practice') {
    return <PracticeTestComponent student={user} onNavigate={navigate} />;
  }

  if (currentView === 'progress') {
    return <ProgressTracker student={user} onNavigate={navigate} />;
  }

  // Other views can be added here
  return <div>Feature coming soon!</div>;
}

export default App;