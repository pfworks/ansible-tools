# Distributed Ansible Tools Setup

## Architecture

```
Client → app-distributed.py (Frontend) → Backend Farm (mTLS encrypted)
                                         ├─ app.py (Backend 1)
                                         ├─ app.py (Backend 2)
                                         └─ app.py (Backend 3)
```

The frontend load balances requests across backends using mutual TLS (mTLS) for encryption.

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

# Edit backends.json with backend URLs (must use https://)
{
  "backends": [
    "https://backend1.example.com:5000",
    "https://backend2.example.com:5000"
  ]
}
```

### 2. Generate SSL Certificates

```bash
./generate-certs.sh
```

This creates:
- `certs/ca-cert.pem` - Certificate Authority
- `certs/server-cert.pem` / `server-key.pem` - Server certificates
- `certs/client-cert.pem` / `client-key.pem` - Client certificates

### 3. Deploy Backend Servers

```bash
ansible-playbook -i inventory.ini deploy.yml
```

This installs:
- Python environment
- Ollama with models
- Backend app with mTLS
- Systemd service

### 4. Deploy Frontend Server

```bash
ansible-playbook -i inventory-frontend.ini deploy-frontend.yml
```

This installs:
- Python environment
- Frontend app
- Backend configuration
- Systemd service

### 5. Configure Infisical Token (Optional)

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

## Security

### mTLS Encryption
- All frontend-to-backend communication uses mutual TLS
- Backends require valid client certificates
- Self-signed CA for internal use

### Certificate Management

Generate user certificates for browser access:
```bash
./generate-user-cert.sh username
```

Revoke compromised certificates:
```bash
./revoke-cert.sh certs/username-cert.pem
```

### Secrets Management
- API keys stored in Infisical
- Only Infisical token in service files
- No secrets in code or git

## Features

### Load Balancing
- Routes to backend with smallest queue
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

Returns aggregate status across all backends.

## Monitoring

Status dashboard available at:
```
http://frontend.example.com:5000/status.html
```

Shows:
- Backend availability
- Queue sizes
- Active tasks
- Real-time graphs

## Notes

- Backends run on port 5000 with HTTPS
- Frontend runs on port 5000 with HTTP (users) and HTTPS (backends)
- All configuration files are in `.gitignore`
- Certificates should be regenerated per environment
