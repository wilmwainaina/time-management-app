import React, { useState, useEffect } from 'react';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import TimeManagementSystem from './components/TimeManagementSystem';
import CreateTask from './components/CreateTask';
import axios from 'axios';
import { API_BASE_URL } from './config';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authView, setAuthView] = useState('login');
  const [currentView, setCurrentView] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    if (token && user) {
      axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(response => {
        setCurrentUser(response.data);
        setIsAuthenticated(true);
      })
      .catch(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      })
      .finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleSignup = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentUser(null);
    setIsAuthenticated(false);
    setCurrentView('dashboard');
  };

  const handleTaskCreated = () => {
    setCurrentView('tasks');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-xl text-gray-700">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return authView === 'login' 
      ? <Login onLogin={handleLogin} switchToSignup={() => setAuthView('signup')} />
      : <Signup onSignup={handleSignup} switchToLogin={() => setAuthView('login')} />;
  }

  const renderView = () => {
    switch(currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'tasks':
        return <TimeManagementSystem user={currentUser} onLogout={handleLogout} />;
      case 'create':
        return <CreateTask onTaskCreated={handleTaskCreated} />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout 
      currentView={currentView}
      setCurrentView={setCurrentView}
      currentUser={currentUser}
      onLogout={handleLogout}
    >
      {renderView()}
    </Layout>
  );
}

export default App;
