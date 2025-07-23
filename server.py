from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import random
import time
import threading
import math
import csv
from io import StringIO
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 用户会话管理
user_sessions = defaultdict(dict)
session_counters = defaultdict(int)

# 模拟MIT-BIH ECG数据生成器（带用户隔离）
def generate_ecg_data(user_id):
    i = 0
    random.seed(user_id)  # 确保不同用户获得不同但可重复的数据
    
    while True:
        # 基础正弦波模拟心跳
        val = math.sin(i * 0.1) * 2
        
        # 添加QRS复合波
        if i % 100 == 0:
            val += random.random() * 5 + 5  # R波
        elif i % 100 == 2 or i % 100 == 98:
            val -= random.random() * 2 + 1  # Q/S波
        
        # 添加P波和T波
        if i % 100 == 90: val += random.random() * 1.5  # P波
        if i % 100 == 15: val += random.random() * 2    # T波
        
        yield val
        i += 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/export/csv')
def export_csv():
    user_id = request.args.get('user_id')
    if not user_id or user_id not in user_sessions:
        return "Invalid session", 400
    
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Time', 'ECG Value'])
    
    ecg_data = user_sessions[user_id].get('ecg_buffer', [])
    sample_rate = 360
    for idx, val in enumerate(ecg_data):
        writer.writerow([idx/sample_rate, val])
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'ecg_export_{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    user_sessions[user_id]['ecg_generator'] = generate_ecg_data(user_id)
    user_sessions[user_id]['ecg_buffer'] = []
    session_counters['total'] += 1
    print(f'User {user_id} connected, total: {session_counters["total"]}')
    emit('connection_status', {'status': 'connected'}, room=user_id)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in user_sessions:
        del user_sessions[user_id]
    session_counters['total'] = max(0, session_counters['total'] - 1)
    print(f'User {user_id} disconnected, total: {session_counters["total"]}')

def broadcast_ecg_data():
    while True:
        current_time = time.time()
        for user_id, session_data in list(user_sessions.items()):
            try:
                if 'last_send_time' not in session_data or current_time - session_data['last_send_time'] >= 1/360:
                    val = next(session_data['ecg_generator'])
                    # 更新用户缓冲区（保留最后5000个点）
                    buffer = session_data.setdefault('ecg_buffer', [])
                    buffer.append(val)
                    if len(buffer) > 5000:
                        buffer.pop(0)
                    
                    socketio.emit('ecg_data', {'value': val, 'timestamp': current_time}, room=user_id)
                    session_data['last_send_time'] = current_time
            except Exception as e:
                print(f"Error for user {user_id}: {str(e)}")
                if user_id in user_sessions:
                    del user_sessions[user_id]
        time.sleep(0.001)  # 减少CPU使用

if __name__ == '__main__':
    # 启动数据广播线程
    threading.Thread(target=broadcast_ecg_data, daemon=True).start()
    print("Starting ECG WebSocket server on http://localhost:8080")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
