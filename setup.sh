#!/bin/bash
set -e

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a suitable model (codellama is good for code generation)
ollama pull codellama:13b

# Create virtual environment and install dependencies
python3 -m venv /export/ollama
/export/ollama/bin/pip install ollama pyyaml flask
