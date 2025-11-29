import React, { useState, useEffect } from 'react';
import { Bell, Clock, X, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';


const TimeManagementSystem = ({ user, onLogout }) => {
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const token = localStorage.getItem('token');
    axios.get(`${API_BASE_URL}/tasks`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(response => setTasks(response.data))
      .catch(error => console.error('Error:', error));
  }, []);

  useEffect(() => {
    const newNotifications = [];
    const now = new Date();
    tasks.forEach(task => {
      if (task.status === 'completed') return;
      const dueDate = new Date(task.due_date);
      const hoursUntilDue = (dueDate - now) / (1000 * 60 * 60);
      if (hoursUntilDue <= 24 && hoursUntilDue > 0) {
        newNotifications.push({
          id: `notif-${task.id}`,
          message: `⚠️ "${task.title}" is due in ${Math.floor(hoursUntilDue)} hours!`
        });
      }
    });
    setNotifications(newNotifications);
  }, [tasks]);

  const toggleTaskStatus = (id) => {
    const task = tasks.find(t => t.id === id);
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    const token = localStorage.getItem('token');
    axios.put(`${API_BASE_URL}/tasks/${id}`, { status: newStatus }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(() => {
        setTasks(tasks.map(t => t.id === id ? { ...t, status: newStatus } : t));
      })
      .catch(error => console.error('Error:', error));
  };

  const deleteTask = (id) => {
    const token = localStorage.getItem('token');
    axios.delete(`${API_BASE_URL}/tasks/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(() => setTasks(tasks.filter(t => t.id !== id)))
      .catch(error => console.error('Error:', error));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const getTimeUntil = (dateString) => {
    const diff = new Date(dateString) - new Date();
    if (diff < 0) return 'Overdue';
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    return days > 0 ? `${days}d ${hours}h` : `${hours}h`;
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'pending') return task.status === 'pending';
    if (filter === 'completed') return task.status === 'completed';
    if (filter === 'urgent') {
      const timeUntil = new Date(task.due_date) - new Date();
      return timeUntil < 24 * 60 * 60 * 1000 && task.status === 'pending';
    }
    return true;
  });

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Simplified Header - Only Bell Button */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-800">My Tasks</h1>
          <button onClick={() => setShowNotifications(!showNotifications)} className="relative p-3 bg-indigo-100 rounded-lg hover:bg-indigo-200 transition">
            <Bell className="text-indigo-600" />
            {notifications.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {notifications.length}
              </span>
            )}
          </button>
        </div>

        {showNotifications && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Notifications</h2>
              <button onClick={() => setShowNotifications(false)}><X className="text-gray-500 hover:text-gray-700" /></button>
            </div>
            {notifications.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No notifications</p>
            ) : (
              <div className="space-y-2">
                {notifications.map(notif => (
                  <div key={notif.id} className="p-3 rounded-lg border-l-4 bg-orange-50 border-orange-500">
                    <p className="text-sm">{notif.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
          <div className="flex gap-2">
            {['all', 'pending', 'urgent', 'completed'].map(f => (
              <button key={f} onClick={() => setFilter(f)} className={`px-4 py-2 rounded-lg font-medium transition ${filter === f ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {filteredTasks.length === 0 ? (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center">
              <p className="text-gray-500 text-lg">No tasks found. Click "Create Task" in the sidebar to add one!</p>
            </div>
          ) : (
            filteredTasks.map(task => (
              <div key={task.id} className={`bg-white rounded-xl shadow-lg p-6 ${task.status === 'completed' ? 'opacity-60' : ''}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <button onClick={() => toggleTaskStatus(task.id)} className="mt-1">
                      {task.status === 'completed' ? (
                        <CheckCircle className="text-green-500" size={24} />
                      ) : (
                        <div className="w-6 h-6 rounded-full border-2 border-gray-300 hover:border-indigo-500" />
                      )}
                    </button>
                    <div className="flex-1">
                      <h3 className={`text-lg font-semibold ${task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-800'}`}>{task.title}</h3>
                      <p className="text-gray-600 mt-1">{task.description}</p>
                      <div className="flex items-center gap-4 mt-3 text-sm">
                        <span className="flex items-center gap-1 text-gray-500"><Clock size={16} />Due: {formatDate(task.due_date)}</span>
                        <span className="flex items-center gap-1 text-gray-500"><AlertCircle size={16} />{getTimeUntil(task.due_date)}</span>
                        <span className={`px-2 py-1 rounded-lg text-xs font-medium border ${getPriorityColor(task.priority)}`}>{task.priority.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>
                  <button onClick={() => deleteTask(task.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg"><X size={20} /></button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};


export default TimeManagementSystem;