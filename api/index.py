from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'timeuser'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'time_management')
}

def get_db():
    return mysql.connector.connect(**db_config)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE user_id = 1 ORDER BY due_date")
        tasks = cursor.fetchall()
        for task in tasks:
            if task.get('due_date'): task['due_date'] = task['due_date'].isoformat()
            if task.get('posted_date'): task['posted_date'] = task['posted_date'].isoformat()
            if task.get('created_at'): task['created_at'] = task['created_at'].isoformat()
            if task.get('updated_at'): task['updated_at'] = task['updated_at'].isoformat()
        cursor.close()
        conn.close()
        return jsonify(tasks)
    
    elif request.method == 'POST':
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (user_id, title, description, due_date, priority, source, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (1, data['title'], data.get('description', ''), data['dueDate'], 
              data.get('priority', 'medium'), data.get('source', 'Manual'), 'pending'))
        conn.commit()
        task_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'id': task_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def task_detail(task_id):
    if request.method == 'PUT':
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", 
                      (data.get('status', 'pending'), task_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'updated'})
    
    elif request.method == 'DELETE':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'deleted'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
