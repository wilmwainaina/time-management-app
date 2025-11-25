from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
from auth import hash_password, verify_password, generate_token, token_required
import csv
from io import StringIO

load_dotenv()
app = Flask(__name__)
CORS(app)

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'timeuser'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'time_management')
}

def get_db():
    return mysql.connector.connect(**db_config)

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration endpoint."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'message': f'{field} is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'message': 'User with this email already exists'}), 400
        
        # Hash password
        password_hash = hash_password(data['password'])
        
        # Create user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (data['username'], data['email'], password_hash))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        # Generate token
        token = generate_token(user_id, data['username'], data['email'])
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': user_id,
                'username': data['username'],
                'email': data['email']
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get user by email
        cursor.execute("""
            SELECT id, username, email, password_hash, role, is_active
            FROM users 
            WHERE email = %s
        """, (data['email'],))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Invalid email or password'}), 401
        
        # Check if account is active
        if not user['is_active']:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Account is deactivated'}), 401
        
        # Verify password
        if not verify_password(data['password'], user['password_hash']):
            cursor.close()
            conn.close()
            return jsonify({'message': 'Invalid email or password'}), 401
        
        # Update last login
        cursor.execute("""
            UPDATE users 
            SET last_login = NOW() 
            WHERE id = %s
        """, (user['id'],))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Generate token
        token = generate_token(user['id'], user['username'], user['email'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me')
@token_required
def get_current_user(user_id):
    """Get current logged-in user info."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, username, email, profile_image, role, created_at, last_login
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Format dates
        if user.get('created_at'):
            user['created_at'] = user['created_at'].isoformat()
        if user.get('last_login'):
            user['last_login'] = user['last_login'].isoformat()
        
        return jsonify(user), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TASK ROUTES (Updated with Authentication)
# ============================================

@app.route('/api/tasks', methods=['GET', 'POST'])
@token_required
def tasks(user_id):
    if request.method == 'GET':
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tasks WHERE user_id = %s ORDER BY due_date", (user_id,))
            tasks = cursor.fetchall()
            
            for task in tasks:
                if task.get('due_date'):
                    task['due_date'] = task['due_date'].isoformat()
                if task.get('posted_date'):
                    task['posted_date'] = task['posted_date'].isoformat()
                if task.get('created_at'):
                    task['created_at'] = task['created_at'].isoformat()
                if task.get('updated_at'):
                    task['updated_at'] = task['updated_at'].isoformat()
            
            cursor.close()
            conn.close()
            return jsonify(tasks)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, title, description, due_date, priority, source, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, data['title'], data.get('description', ''), 
                  data['dueDate'], data.get('priority', 'medium'), 
                  data.get('source', 'Manual'), 'pending'))
            conn.commit()
            task_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return jsonify({'id': task_id, 'message': 'Task created'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@token_required
def task_detail(user_id, task_id):
    if request.method == 'PUT':
        try:
            data = request.json
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks 
                SET status = %s
                WHERE id = %s AND user_id = %s
            """, (data.get('status', 'pending'), task_id, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Task updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Task deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard-stats')
@token_required
def dashboard_stats(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
        all_tasks = cursor.fetchall()
        
        total = len(all_tasks)
        completed = len([t for t in all_tasks if t['status'] == 'completed'])
        in_progress = len([t for t in all_tasks if t['status'] == 'in_progress'])
        
        overdue = 0
        for task in all_tasks:
            if task['status'] != 'completed' and task['due_date'] < datetime.now():
                overdue += 1
        
        high_count = len([t for t in all_tasks if t['priority'] == 'high'])
        medium_count = len([t for t in all_tasks if t['priority'] == 'medium'])
        low_count = len([t for t in all_tasks if t['priority'] == 'low'])
        
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        recent_tasks = cursor.fetchall()
        
        for task in recent_tasks:
            if task.get('due_date'):
                task['due_date'] = task['due_date'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'stats': {
                'total': total,
                'completed': completed,
                'inProgress': in_progress,
                'overdue': overdue
            },
            'chartData': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            },
            'recentTasks': recent_tasks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health')
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
