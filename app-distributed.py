#!/export/ollama/bin/python3
from flask import Flask, request, jsonify, send_from_directory
import requests
import json
from queue import Queue, PriorityQueue
from threading import Thread, Lock
import time
import uuid
import os

app = Flask(__name__)

# Load backends from config file
def load_backends():
    config_file = os.path.join(os.path.dirname(__file__), 'backends.json')
    try:
        with open(config_file, 'r') as f:
            return json.load(f)['backends']
    except:
        return ['http://localhost:5001']

BACKENDS = load_backends()

# Track backend availability and queue size
backend_status = {url: {'available': True, 'queue_size': 0} for url in BACKENDS}
backend_lock = Lock()

def get_backend_queue_size(url):
    """Check backend queue size"""
    try:
        resp = requests.get(f"{url}/queue-status", timeout=2)
        return resp.json().get('queue_size', 999)
    except:
        return 999

def get_available_backend():
    """Get backend with lowest queue"""
    with backend_lock:
        # Update queue sizes
        for url in BACKENDS:
            if backend_status[url]['available']:
                backend_status[url]['queue_size'] = get_backend_queue_size(url)
        
        # Find backend with lowest queue
        available = [(url, backend_status[url]['queue_size']) 
                     for url in BACKENDS if backend_status[url]['available']]
        
        if not available:
            return None
        
        best_backend = min(available, key=lambda x: x[1])[0]
        backend_status[best_backend]['available'] = False
        return best_backend

def release_backend(url):
    """Mark backend as available"""
    with backend_lock:
        backend_status[url]['available'] = True

def proxy_request(endpoint, data):
    """Send request to available backend"""
    backend = get_available_backend()
    if not backend:
        return {'error': 'No backends available'}, 503
    
    try:
        response = requests.post(f"{backend}{endpoint}", json=data, timeout=600)
        result = response.json()
        return result, response.status_code
    except Exception as e:
        return {'error': f'Backend error: {str(e)}'}, 500
    finally:
        release_backend(backend)

def split_and_process(commands, model, chunk_size=10):
    """Split commands into chunks and process in parallel"""
    lines = commands.strip().split('\n')
    if len(lines) <= chunk_size:
        return proxy_request('/generate', {'commands': commands, 'model': model})
    
    # Split into chunks
    chunks = ['\n'.join(lines[i:i+chunk_size]) for i in range(0, len(lines), chunk_size)]
    results = []
    threads = []
    
    def process_chunk(chunk, idx):
        result, _ = proxy_request('/generate', {'commands': chunk, 'model': model})
        results.append((idx, result))
    
    for idx, chunk in enumerate(chunks):
        t = Thread(target=process_chunk, args=(chunk, idx))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    # Combine results
    results.sort(key=lambda x: x[0])
    combined = '\n---\n'.join([r[1].get('playbook', '') for r in results])
    total_time = sum([r[1].get('elapsed', 0) for r in results])
    
    return {
        'playbook': combined,
        'elapsed': round(max([r[1].get('elapsed', 0) for r in results]), 2),
        'total_tokens': sum([r[1].get('total_tokens', 0) for r in results]),
        'chunks_processed': len(chunks)
    }, 200

@app.route('/')
def index():
    return send_from_directory('/export/html', 'index.html')

@app.route('/status')
def status_page():
    return send_from_directory('/export/html', 'status.html')

@app.route('/queue-status')
def queue_status():
    """Aggregate queue status from all backends"""
    backends_info = []
    total_queue = 0
    active_count = 0
    
    for backend in BACKENDS:
        try:
            resp = requests.get(f"{backend}/queue-status", timeout=2)
            data = resp.json()
            queue_size = data.get('queue_size', 0)
            total_queue += queue_size
            is_active = data.get('active', False)
            if is_active:
                active_count += 1
            
            backends_info.append({
                'url': backend,
                'queue_size': queue_size,
                'active': is_active,
                'status': 'online'
            })
        except:
            backends_info.append({
                'url': backend,
                'queue_size': 0,
                'active': False,
                'status': 'offline'
            })
    
    return jsonify({
        'queue_size': total_queue,
        'active': active_count > 0,
        'active_backends': active_count,
        'total_backends': len(BACKENDS),
        'backends': backends_info
    })

@app.route('/generate', methods=['POST'])
def generate():
    commands = request.json.get('commands', '')
    model = request.json.get('model', 'codellama:13b')
    split = request.json.get('split', False)
    
    if split:
        result, status = split_and_process(commands, model)
    else:
        result, status = proxy_request('/generate', {'commands': commands, 'model': model})
    
    return jsonify(result), status

@app.route('/explain', methods=['POST'])
def explain():
    playbook = request.json.get('playbook', '')
    model = request.json.get('model', 'codellama:13b')
    result, status = proxy_request('/explain', {'playbook': playbook, 'model': model})
    return jsonify(result), status

@app.route('/generate-code', methods=['POST'])
def generate_code_endpoint():
    description = request.json.get('description', '')
    model = request.json.get('model', 'codellama:13b')
    result, status = proxy_request('/generate-code', {'description': description, 'model': model})
    return jsonify(result), status

@app.route('/explain-code', methods=['POST'])
def explain_code_endpoint():
    code = request.json.get('code', '')
    model = request.json.get('model', 'codellama:13b')
    result, status = proxy_request('/explain-code', {'code': code, 'model': model})
    return jsonify(result), status

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    commands = file.read().decode('utf-8')
    model = request.form.get('model', 'codellama:13b')
    
    result, status = proxy_request('/generate', {'commands': commands, 'model': model})
    return jsonify(result), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
