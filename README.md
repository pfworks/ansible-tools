# Shell to Ansible Playbook Generator

Local LLM-powered tool to automatically convert shell commands into Ansible playbooks and explain existing playbooks.

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

### Web Interface

Start the web server:
```bash
chmod +x app.py
./app.py
```

Then open http://your-server:5000 in your browser.

**Two Services Available:**

1. **Shell Commands → Ansible Playbook**
   - Paste shell commands or upload a file
   - Generate Ansible playbook with one click
   - YAML validation with automatic retries

2. **Ansible Playbook → Explanation**
   - Paste or upload an Ansible playbook
   - Get a clear explanation of what it does
   - Understand each task and its purpose

Features:
- Copy or download generated content
- View generation time and token statistics
- Request queuing (one generation at a time)

### API - JSON Endpoint

**Generate playbook from commands:**
```bash
# Get full response with stats
curl -X POST http://your-server:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"commands": "apt-get update\napt-get install -y nginx"}'

# Extract just the playbook
curl -X POST http://your-server:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"commands": "'"$(cat commands.txt)"'"}' \
  | jq -r '.playbook' > playbook.yml
```

**Explain a playbook:**
```bash
curl -X POST http://your-server:5000/explain \
  -H "Content-Type: application/json" \
  -d '{"playbook": "'"$(cat playbook.yml)"'"}' \
  | jq -r '.explanation'
```

### API - File Upload Endpoint

**Upload commands file:**
```bash
# Upload and get full JSON response
curl -X POST http://your-server:5000/upload \
  -F "file=@commands.txt"

# Upload and save just the playbook
curl -X POST http://your-server:5000/upload \
  -F "file=@commands.txt" \
  | jq -r '.playbook' > playbook.yml
```

### Command Line

```bash
./shell_to_ansible.py example_commands.txt > playbook.yml
```

## Response Format

All endpoints return JSON with:
- `playbook` or `explanation`: Generated content
- `elapsed`: Generation time in seconds
- `prompt_tokens`: Input tokens processed
- `response_tokens`: Output tokens generated
- `total_tokens`: Total tokens
- `error`: Present only if YAML validation failed (after 3 retries)

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
- Python 3.8+
- 8-12 vCPUs recommended for better performance

## Model Options

Default: `codellama:13b` (good balance)
- Smaller/faster: `codellama:7b` (uses ~4GB RAM)
- Larger/better: `codellama:34b` (requires 32GB+ RAM)

Change model in `app.py` and pull with `ollama pull <model>`

## Features

- **Dual functionality**: Generate playbooks OR explain them
- **Request queuing**: Processes one generation at a time
- **YAML validation**: Automatic retries for invalid output
- **Token usage statistics**: Track model performance
- **Performance timing**: See how long each generation takes
- **Web UI and API access**: Use via browser or programmatically
- **Cross-platform**: Works on Linux and macOS
- **File upload support**: Upload .txt, .sh, .yml, .yaml files

## Files

- `app.py` - Flask web server and API
- `index.html` - Web interface
- `shell_to_ansible.py` - Command-line tool
- `setup.sh` - Installation script
- `deploy.yml` - Ansible deployment playbook
- `inventory.ini` - Ansible inventory template
- `ansible-ollama.service` - Linux systemd service
- `com.ooma.ansible-ollama.plist` - macOS LaunchDaemon
