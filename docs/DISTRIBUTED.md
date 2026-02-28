# Distributed Ansible Tools Setup

## Architecture

```
Client → app-distributed.py (Frontend) → Backend Farm
                                         ├─ app.py (Backend 1)
                                         ├─ app.py (Backend 2)
                                         └─ app.py (Backend 3)
```

The frontend load balances requests across backends with weighted priority.

## Initial Setup

### 1. Create Configuration Files

```bash
# Copy example files
cp inventory.ini.example inventory.ini
cp inventory-frontend.ini.example inventory-frontend.ini
cp backends.json.example backends.json

# Edit inventory.ini with your backend servers
[servers]
backend1.example.com ansible_user=root
backend2.example.com ansible_user=root

# Edit inventory-frontend.ini with your frontend server
[frontend]
frontend.example.com ansible_user=root

# Edit backends.json with backend URLs and weights
{
  "backends": [
    {"url": "http://backend1.example.com:5000", "weight": 1},
    {"url": "http://backend2.example.com:5000", "weight": 10}
  ]
}
```

Higher weight = higher priority. Backend with weight 10 will be preferred 10x over weight 1.

### 2. Deploy Backend Servers

```bash
ansible-playbook -i inventory.ini deploy.yml
```

This installs:
- Python environment
- Ollama with models
- Backend app
- Systemd service

### 3. Deploy Frontend Server

```bash
ansible-playbook -i inventory-frontend.ini deploy-frontend.yml
```

This installs:
- Python environment
- Frontend app
- Backend configuration
- Systemd service

### 4. Configure Infisical Token (Optional)

For Claude API fallback, set the Infisical token on each backend:

```bash
ssh root@backend1.example.com
systemctl edit ansible-ollama
```

Add:
```
[Service]
Environment="INFISICAL_TOKEN=your-token-here"
```

Restart:
```bash
systemctl restart ansible-ollama
```

## Features

### Weighted Load Balancing
- Routes to backend with best weighted score
- Score = queue_size - (weight * 0.1)
- Higher weight backends preferred when queues equal
- Tracks backend availability
- Automatic failover

### Claude API Fallback
- Backends fallback to Claude if Ollama fails or produces low-quality output
- Configured via environment variables
- API key fetched from Infisical

### Queue Status
```bash
curl http://frontend.example.com:5000/queue-status
```

Returns aggregate status across all backends including weights.

## Monitoring

Status dashboard available at:
```
http://frontend.example.com:5000/status.html
```

Shows:
- Backend availability
- Queue sizes
- Backend weights
- Active tasks
- Real-time graphs

## Notes

- All services run on port 5000 with HTTP
- Frontend accepts HTTP from users
- Frontend to backend communication is HTTP
- All configuration files are in `.gitignore`
- Weights can be adjusted in `backends.json` and service restarted
