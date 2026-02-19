#!/export/ollama/bin/python3
from flask import Flask, request, jsonify, send_from_directory
import ollama
from queue import Queue
from threading import Thread

app = Flask(__name__)
task_queue = Queue()

def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        task_type = task.get('type')
        if task_type == 'explain':
            task['result'] = explain_playbook(task['playbook'])
        elif task_type == 'generate_code':
            task['result'] = generate_code(task['description'])
        elif task_type == 'explain_code':
            task['result'] = explain_code(task['code'])
        else:
            task['result'] = generate_playbook(task['commands'])
        task_queue.task_done()

def generate_playbook(commands):
    import time
    import yaml
    
    start_time = time.time()
    
    prompt = f"""Convert these shell commands into an Ansible playbook. Return ONLY valid YAML, no explanations:

Commands:
{commands}

Generate a complete Ansible playbook with proper tasks."""

    max_retries = 3
    for attempt in range(max_retries):
        response = ollama.chat(model='codellama:13b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        playbook_text = response['message']['content']
        
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

def explain_playbook(playbook):
    import time
    
    start_time = time.time()
    
    prompt = f"""Explain what this Ansible playbook does in clear, simple language. Describe each task and its purpose:

{playbook}"""

    response = ollama.chat(model='codellama:13b', messages=[
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

def generate_code(description):
    import time
    
    start_time = time.time()
    
    prompt = f"""Generate clean, well-commented code based on this description. Include the language and provide working code:

{description}"""

    response = ollama.chat(model='codellama:13b', messages=[
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

def explain_code(code):
    import time
    
    start_time = time.time()
    
    prompt = f"""Explain what this code does in clear, simple language. Describe the logic, functions, and purpose:

{code}"""

    response = ollama.chat(model='codellama:13b', messages=[
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

@app.route('/generate', methods=['POST'])
def generate():
    commands = request.json.get('commands', '')
    
    task = {'commands': commands, 'result': None}
    task_queue.put(task)
    task_queue.join()
    
    return jsonify(task['result'])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    commands = file.read().decode('utf-8')
    
    task = {'commands': commands, 'result': None}
    task_queue.put(task)
    task_queue.join()
    
    return jsonify(task['result'])

@app.route('/explain', methods=['POST'])
def explain():
    playbook = request.json.get('playbook', '')
    
    task = {'playbook': playbook, 'result': None, 'type': 'explain'}
    task_queue.put(task)
    task_queue.join()
    
    return jsonify(task['result'])

@app.route('/generate-code', methods=['POST'])
def generate_code_endpoint():
    description = request.json.get('description', '')
    
    task = {'description': description, 'result': None, 'type': 'generate_code'}
    task_queue.put(task)
    task_queue.join()
    
    return jsonify(task['result'])

@app.route('/explain-code', methods=['POST'])
def explain_code_endpoint():
    code = request.json.get('code', '')
    
    task = {'code': code, 'result': None, 'type': 'explain_code'}
    task_queue.put(task)
    task_queue.join()
    
    return jsonify(task['result'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
