# Distributed Ansible Tools Setup

## Architecture

```
Client → app-distributed.py (port 5000) → Backend Farm
                                          ├─ app.py (port 5001)
                                          ├─ app.py (port 5002)
                                          └─ app.py (port 5003)
```

## Setup

### 1. Configure Backend Servers

Edit `app-distributed.py` and set your backend URLs:

```python
BACKENDS = [
    'http://server1.local:5001',
    'http://server2.local:5001',
    'http://server3.local:5001',
]
```

### 2. Start Backend Workers

On each backend machine, run the original app.py on different ports:

```bash
# Machine 1
python3 app.py  # runs on port 5000

# Machine 2
PORT=5001 python3 app.py

# Machine 3
PORT=5002 python3 app.py
```

Or modify app.py to use different ports.

### 3. Start Load Balancer

```bash
python3 app-distributed.py
```

## Features

### Load Balancing
- Automatically routes requests to available backends
- Tracks backend availability
- Returns error if all backends busy

### Parallel Processing (Optional)
Split large command sets across multiple backends:

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"commands": "...", "model": "codellama:13b", "split": true}'
```

When `split: true`:
- Commands split into chunks of 10 lines
- Each chunk processed on different backend
- Results combined and returned
- Faster for large command sets

### Queue Status
Shows aggregate status across all backends:

```bash
curl http://localhost:5000/queue-status
```

Returns:
```json
{
  "queue_size": 5,
  "active": true,
  "active_backends": 2,
  "total_backends": 3
}
```

## Use Cases

1. **High Availability**: Multiple backends handle failures
2. **Parallel Processing**: Split large tasks across machines
3. **Load Distribution**: Balance requests across GPU/CPU resources
4. **Scaling**: Add more backends as needed

## Configuration Options

Edit `app-distributed.py`:

- `BACKENDS`: List of backend URLs
- `chunk_size=10`: Lines per chunk for split processing
- `timeout=600`: Request timeout in seconds

## Notes

- Backends must run the original `app.py`
- Each backend needs Ollama with models installed
- Split mode works best for independent command sets
- Not all tasks benefit from splitting (explanations don't split well)
