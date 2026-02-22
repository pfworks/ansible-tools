# Ansible Tools

Local LLM-powered tool to automatically convert shell commands into Ansible playbooks, explain existing playbooks, generate code, and explain code.

## Quick Deploy

Deploy to a new machine using Ansible:

```bash
# Edit inventory.ini with your target host(s)
ansible-playbook -i inventory.ini deploy.yml
```

This will:
- Install all dependencies (Python, Ollama, etc.)
- Create virtual environment and install packages
- Pull the CodeLlama 13B model
- Deploy the web application
- Set up systemd service (Linux) or LaunchDaemon (macOS)
- Open firewall port 5000

Works on Ubuntu/Debian Linux and macOS.

## Manual Setup

```bash
chmod +x setup.sh
./setup.sh
```

## Usage

### CLI Tool

Install the CLI tool:
```bash
sudo cp ansible-tools /usr/local/bin/
chmod +x /usr/local/bin/ansible-tools
```

Set environment variables:
```bash
export ANSIBLE_TOOLS_API=http://ansible.corp.ooma.com:5000
export ANSIBLE_TOOLS_MODEL=codellama:13b
```

**File-based commands:**
```bash
# Convert shell commands to Ansible playbook
ansible-tools shell2ansible commands.txt > playbook.yml

# Explain an Ansible playbook
ansible-tools explain-ansible playbook.yml

# Generate code from description
ansible-tools generate-code description.txt > script.py

# Explain code
ansible-tools explain-code script.py
```

**Interactive chat mode:**
```bash
ansible-tools chat
```

In chat mode:
- Choose a mode (shell2ansible, explain-ansible, generate-code, explain-code)
- Paste/type your input
- Press Ctrl+D to submit
- Get results with timing and token stats
- Shows queue position if other requests are processing

### Web Interface

Start the web server:
```bash
chmod +x app.py
./app.py
```

Then open http://your-server:5000 in your browser.

**Four Services Available:**

1. **Shell Commands → Ansible Playbook**
   - Paste shell commands or upload a file
   - Generate Ansible playbook with one click
   - YAML validation with automatic retries
   - Strips markdown code blocks automatically

2. **Ansible Playbook → Explanation**
   - Paste or upload an Ansible playbook
   - Get a clear explanation of what it does
   - Understand each task and its purpose

3. **Description → Code**
   - Describe what you want in plain language
   - Generate working code with comments
   - Supports multiple programming languages

4. **Code → Explanation**
   - Paste any code
   - Get a clear explanation of what it does
   - Understand logic, functions, and purpose

Features:
- Model selection (7B, 13B, 34B) with RAM requirements
- Copy or download generated content
- View generation time and token statistics
- Request queuing with position display
- Queue status shown before and after processing
- Each request returns independently (no waiting for all tasks)

### API - JSON Endpoint

**Generate playbook from commands:**
```bash
curl -X POST http://your-server:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"commands": "apt-get update\napt-get install -y nginx", "model": "codellama:13b"}'
```

**Explain a playbook:**
```bash
curl -X POST http://your-server:5000/explain \
  -H "Content-Type: application/json" \
  -d '{"playbook": "'"$(cat playbook.yml)"'", "model": "codellama:13b"}'
```

**Generate code:**
```bash
curl -X POST http://your-server:5000/generate-code \
  -H "Content-Type: application/json" \
  -d '{"description": "Python script to parse CSV files", "model": "codellama:13b"}'
```

**Explain code:**
```bash
curl -X POST http://your-server:5000/explain-code \
  -H "Content-Type: application/json" \
  -d '{"code": "'"$(cat script.py)"'", "model": "codellama:13b"}'
```

**Check queue status:**
```bash
curl http://your-server:5000/queue-status
```

Returns:
- `queue_size`: Total items (active + waiting)
- `active`: true/false if something is processing
- `active_type`: Type of active task
- `active_model`: Model being used

### API - File Upload Endpoint

**Upload commands file:**
```bash
curl -X POST http://your-server:5000/upload \
  -F "file=@commands.txt" \
  -F "model=codellama:13b"
```

## Response Format

All endpoints return JSON with:
- `playbook`, `explanation`, or `code`: Generated content
- `elapsed`: Generation time in seconds
- `prompt_tokens`: Input tokens processed
- `response_tokens`: Output tokens generated
- `total_tokens`: Total tokens
- `queue_position`: Position in queue (if queued)
- `error`: Present only if generation failed

## Model Selection

Available models:
- `codellama:7b` - Fast, ~4GB RAM
- `codellama:13b` - Balanced, ~8GB RAM (default)
- `codellama:34b` - Best quality, ~20GB RAM (requires 48GB+ total system RAM)

Specify model in:
- Web UI: Dropdown selector
- CLI: `ANSIBLE_TOOLS_MODEL` environment variable
- API: `model` parameter in JSON

To use a model, pull it first:
```bash
ollama pull codellama:13b
```

## Queue System

- Requests are processed one at a time (serialized)
- Queue position shown when submitting
- Each request returns as soon as its task completes
- Active task and queue size visible via `/queue-status`
- Web UI shows: "Queue position: #2 - Generating..."
- CLI shows: "Queue position: #2" then "Generating..."

## Systemd Service (Linux)

Install as a system service:
```bash
sudo cp ansible-ollama.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ansible-ollama
sudo systemctl start ansible-ollama
sudo systemctl status ansible-ollama
```

## LaunchDaemon (macOS)

Install as a system service:
```bash
sudo cp com.ooma.ansible-ollama.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.ooma.ansible-ollama.plist
```

## Requirements

- Ubuntu/Debian Linux or macOS
- 16GB+ RAM (for 13B model)
- 48GB+ RAM (for 34B model)
- Python 3.8+
- 8-12 vCPUs recommended for better performance

## Performance

**CodeLlama 13B (16GB RAM):**
- Generation time: 20-40 seconds
- Concurrent users: 1-2 comfortably

**CodeLlama 34B (48GB+ RAM):**
- Generation time: 2-5 minutes
- Higher quality output
- Better for complex tasks

## Features

- **Four AI services**: Generate playbooks, explain playbooks, generate code, explain code
- **Multiple interfaces**: Web UI, CLI tool, REST API
- **Request queuing**: Serialized processing with position tracking
- **Model selection**: Choose speed vs quality
- **YAML validation**: Automatic retries for invalid output
- **Markdown stripping**: Cleans code blocks from output
- **Token statistics**: Track model performance
- **Performance timing**: See generation duration
- **Queue visibility**: Know your position and wait time
- **Cross-platform**: Works on Linux and macOS
- **File upload support**: Upload .txt, .sh, .yml, .yaml files

## Files

- `app.py` - Flask web server and API
- `ansible-tools` - CLI tool for command-line usage
- `index.html` - Web interface
- `shell_to_ansible.py` - Legacy command-line tool
- `setup.sh` - Installation script
- `deploy.yml` - Ansible deployment playbook
- `inventory.ini` - Ansible inventory template
- `ansible-ollama.service` - Linux systemd service
- `com.ooma.ansible-ollama.plist` - macOS LaunchDaemon
