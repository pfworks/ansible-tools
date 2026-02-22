# Ansible Tools Release

This release includes all components for deploying Ansible Tools in distributed or standalone mode.

## Contents

### Core Files
- `app.py` - Backend worker application
- `app-distributed.py` - Frontend load balancer
- `index.html` - Web interface
- `ansible-tools` - CLI tool

### Deployment
- `deploy.yml` - Deploy backend workers (includes all 4 models)
- `deploy-frontend.yml` - Deploy frontend load balancer
- `inventory.ini` - Ansible inventory template
- `setup.sh` - Manual installation script

### Services
- `ansible-ollama.service` - Systemd service for backend
- `ansible-ollama-frontend.service` - Systemd service for frontend

### Documentation
- `README.md` - Main documentation
- `DISTRIBUTED.md` - Distributed setup guide

## Quick Start

### Standalone Backend
```bash
# Edit inventory.ini with backend host
ansible-playbook -i inventory.ini deploy.yml
```

### Distributed Setup
```bash
# Deploy backends
ansible-playbook -i inventory.ini deploy.yml

# Edit app-distributed.py BACKENDS list
# Deploy frontend
ansible-playbook -i inventory-frontend.ini deploy-frontend.yml
```

## Models Included

Backend deployment pulls all 4 models:
- codellama:7b (~4GB RAM)
- codellama:13b (~8GB RAM)
- codellama:13b (~20GB RAM)
- codellama:70b (~40GB RAM)

## System Requirements

**Backend:**
- 16GB+ RAM (for 7b/13b models)
- 48GB+ RAM (for 34b model)
- 80GB+ RAM (for 70b model)
- Python 3.8+
- Ollama

**Frontend:**
- 1-2GB RAM
- 1-2 vCPUs
- Python 3.8+
- No Ollama needed
