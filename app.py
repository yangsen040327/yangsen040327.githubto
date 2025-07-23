from flask import Flask, render_template
from flask_socketio import SocketIO
import numpy as np
import time
import threading
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 模拟MIT-BIH ECG数据生成器
class ECGGenerator:
    def __init__(self):
        self.sample_rate = 360
        self.running = False
        self.leads = ['MLII', 'V1', 'V2', 'V5']
        
    def generate_ecg_point(self):
        t = time.time()
        points = []
        
        for lead in self.leads:
            # 基础心率
            value = 0.5 * np.sin(2 * np.pi * 1 * t)
            
            # 添加导联特异性变化
            if lead == 'MLII':
                value += 0.3 * np.sin(2 * np.pi * 0.3 * t)
            elif lead == 'V1':
                value += 0.2 * np.cos(2 * np.pi * 0.4 * t)
            elif lead == 'V2':
                value += 0.25 * np.sin(2 * np.pi * 0.35 * t)
            elif lead == 'V5':
                value += 0.15 * np.cos(2 * np.pi * 0.25 * t)
            
            # 添加QRS复合波
            if int(t * 1.2) % 2 == 0:  # 大约1.2秒一个心跳
                phase = (t * 1.2) % 1
                if 0 < phase < 0.1:
                    value += 5 * np.exp(-50 * (phase - 0.05)**2)  # R波
            
            # 添加噪声
            value += random.gauss(0, 0.05)
            
            points.append({
                'timestamp': int(t * 1000),
                'lead': lead,
                'value': value
            })
        
        return points
    
    def start(self):
        self.running = True
        def generate():
            while self.running:
                points = self.generate_ecg_point()
                socketio.emit('ecg_data', points)
                time.sleep(1.0 / self.sample_rate)
        
        thread = threading.Thread(target=generate)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        self.running = False

ecg_gen = ECGGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    if not ecg_gen.running:
        ecg_gen.start()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
