#!/export/ollama/bin/python3
from flask import Flask, request, jsonify, send_from_directory
import ollama
from queue import Queue
from threading import Thread, Event
import uuid

app = Flask(__name__)
task_queue = Queue()
active_task = None
task_results = {}

def worker():
    global active_task
    while True:
        task = task_queue.get()
        if task is None:
            break
        active_task = task
        task_id = task['id']
        task_type = task.get('type')
        model = task.get('model', 'codellama:13b')
        
        if task_type == 'explain':
            result = explain_playbook(task['playbook'], model)
        elif task_type == 'generate_code':
            result = generate_code(task['description'], model)
        elif task_type == 'explain_code':
            result = explain_code(task['code'], model)
        else:
            result = generate_playbook(task['commands'], model)
        
        task_results[task_id] = result
        task['event'].set()
        active_task = None
        task_queue.task_done()

def generate_playbook(commands, model='codellama:13b'):
    import time
    import yaml
    import re
    
    # Check if model exists
    try:
        ollama.show(model)
    except:
        return {
            'playbook': '',
            'elapsed': 0,
            'error': f'Model {model} not found. Please run: ollama pull {model}',
            'prompt_tokens': 0,
            'response_tokens': 0,
            'total_tokens': 0
        }
    
    start_time = time.time()
    
    prompt = f"""Convert these shell commands into an Ansible playbook. Return ONLY valid YAML, no explanations:

Commands:
{commands}

Generate a complete Ansible playbook with proper tasks."""

    max_retries = 3
    for attempt in range(max_retries):
        response = ollama.chat(model=model, messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        playbook_text = response['message']['content']
        
        # Strip markdown code blocks (handle multiple variations)
        import re
        # Remove opening code fence with optional language
        playbook_text = re.sub(r'^```[a-z]*\s*\n', '', playbook_text, flags=re.MULTILINE)
        # Remove closing code fence
        playbook_text = re.sub(r'\n```\s*$', '', playbook_text, flags=re.MULTILINE)
        # Remove any remaining backticks at start/end
        playbook_text = playbook_text.strip('`').strip()
        
        # Validate YAML
        try:
            yaml.safe_load(playbook_text)
            break  # Valid YAML, exit retry loop
        except yaml.YAMLError as e:
            if attempt == max_retries - 1:
                return {
                    'playbook': playbook_text,
                    'elapsed': round(time.time() - start_time, 2),
                    'error': f'Invalid YAML after {max_retries} attempts: {str(e)}',
                    'prompt_tokens': response.get('prompt_eval_count', 0),
                    'response_tokens': response.get('eval_count', 0),
                    'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
                }
    
    elapsed = time.time() - start_time
    
    return {
        'playbook': playbook_text,
        'elapsed': round(elapsed, 2),
        'prompt_tokens': response.get('prompt_eval_count', 0),
        'response_tokens': response.get('eval_count', 0),
        'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
    }

def explain_playbook(playbook, model='codellama:13b'):
    import time
    
    # Check if model exists
    try:
        ollama.show(model)
    except:
        return {
            'explanation': '',
            'elapsed': 0,
            'error': f'Model {model} not found. Please run: ollama pull {model}',
            'prompt_tokens': 0,
            'response_tokens': 0,
            'total_tokens': 0
        }
    
    start_time = time.time()
    
    prompt = f"""Explain what this Ansible playbook does in clear, simple language. Describe each task and its purpose:

{playbook}"""

    response = ollama.chat(model=model, messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    elapsed = time.time() - start_time
    
    return {
        'explanation': response['message']['content'],
        'elapsed': round(elapsed, 2),
        'prompt_tokens': response.get('prompt_eval_count', 0),
        'response_tokens': response.get('eval_count', 0),
        'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
    }

def generate_code(description, model='codellama:13b'):
    import time
    
    # Check if model exists
    try:
        ollama.show(model)
    except:
        return {
            'code': '',
            'elapsed': 0,
            'error': f'Model {model} not found. Please run: ollama pull {model}',
            'prompt_tokens': 0,
            'response_tokens': 0,
            'total_tokens': 0
        }
    
    start_time = time.time()
    
    prompt = f"""Generate clean, well-commented code based on this description. Include the language and provide working code:

{description}"""

    response = ollama.chat(model=model, messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    elapsed = time.time() - start_time
    
    return {
        'code': response['message']['content'],
        'elapsed': round(elapsed, 2),
        'prompt_tokens': response.get('prompt_eval_count', 0),
        'response_tokens': response.get('eval_count', 0),
        'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
    }

def explain_code(code, model='codellama:13b'):
    import time
    
    # Check if model exists
    try:
        ollama.show(model)
    except:
        return {
            'explanation': '',
            'elapsed': 0,
            'error': f'Model {model} not found. Please run: ollama pull {model}',
            'prompt_tokens': 0,
            'response_tokens': 0,
            'total_tokens': 0
        }
    
    start_time = time.time()
    
    prompt = f"""Explain what this code does in clear, simple language. Describe the logic, functions, and purpose:

{code}"""

    response = ollama.chat(model=model, messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    elapsed = time.time() - start_time
    
    return {
        'explanation': response['message']['content'],
        'elapsed': round(elapsed, 2),
        'prompt_tokens': response.get('prompt_eval_count', 0),
        'response_tokens': response.get('eval_count', 0),
        'total_tokens': response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
    }

Thread(target=worker, daemon=True).start()

@app.route('/')
def index():
    return send_from_directory('/export/html', 'index.html')

@app.route('/queue-status')
def queue_status():
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    status = {
        'queue_size': queue_size,
        'active': active_task is not None
    }
    
    if active_task:
        status['active_type'] = active_task.get('type', 'generate')
        status['active_model'] = active_task.get('model', 'unknown')
    
    return jsonify(status)

@app.route('/generate', methods=['POST'])
def generate():
    commands = request.json.get('commands', '')
    model = request.json.get('model', 'codellama:13b')
    
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    task_id = str(uuid.uuid4())
    event = Event()
    task = {'id': task_id, 'commands': commands, 'model': model, 'event': event}
    task_queue.put(task)
    
    event.wait()
    result = task_results.pop(task_id)
    
    if queue_size > 0:
        result['queue_position'] = queue_size + 1
    
    return jsonify(result)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    commands = file.read().decode('utf-8')
    model = request.form.get('model', 'codellama:13b')
    
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    task_id = str(uuid.uuid4())
    event = Event()
    task = {'id': task_id, 'commands': commands, 'model': model, 'event': event}
    task_queue.put(task)
    
    event.wait()
    result = task_results.pop(task_id)
    
    if queue_size > 0:
        result['queue_position'] = queue_size + 1
    
    return jsonify(result)

@app.route('/explain', methods=['POST'])
def explain():
    playbook = request.json.get('playbook', '')
    model = request.json.get('model', 'codellama:13b')
    
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    task_id = str(uuid.uuid4())
    event = Event()
    task = {'id': task_id, 'playbook': playbook, 'model': model, 'event': event, 'type': 'explain'}
    task_queue.put(task)
    
    event.wait()
    result = task_results.pop(task_id)
    
    if queue_size > 0:
        result['queue_position'] = queue_size + 1
    
    return jsonify(result)

@app.route('/generate-code', methods=['POST'])
def generate_code_endpoint():
    description = request.json.get('description', '')
    model = request.json.get('model', 'codellama:13b')
    
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    task_id = str(uuid.uuid4())
    event = Event()
    task = {'id': task_id, 'description': description, 'model': model, 'event': event, 'type': 'generate_code'}
    task_queue.put(task)
    
    event.wait()
    result = task_results.pop(task_id)
    
    if queue_size > 0:
        result['queue_position'] = queue_size + 1
    
    return jsonify(result)

@app.route('/explain-code', methods=['POST'])
def explain_code_endpoint():
    code = request.json.get('code', '')
    model = request.json.get('model', 'codellama:13b')
    
    queue_size = task_queue.qsize()
    if active_task is not None:
        queue_size += 1
    
    task_id = str(uuid.uuid4())
    event = Event()
    task = {'id': task_id, 'code': code, 'model': model, 'event': event, 'type': 'explain_code'}
    task_queue.put(task)
    
    event.wait()
    result = task_results.pop(task_id)
    
    if queue_size > 0:
        result['queue_position'] = queue_size + 1
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
