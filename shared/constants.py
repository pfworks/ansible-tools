"""Shared constants for sheLLaMa CLI and API."""
import re

CLOUD_PRICING = {
    'Claude 4 Sonnet':    {'input': 3.00,  'output': 15.00},
    'Claude 4 Haiku':     {'input': 0.80,  'output': 4.00},
    'Claude 3.5 Sonnet':  {'input': 3.00,  'output': 15.00},
    'GPT-4o':             {'input': 2.50,  'output': 10.00},
    'GPT-4o mini':        {'input': 0.15,  'output': 0.60},
    'OpenAI o3':          {'input': 10.00, 'output': 40.00},
    'OpenAI o4-mini':     {'input': 1.10,  'output': 4.40},
    'Azure GPT-4o':       {'input': 2.50,  'output': 10.00},
    'Gemini 2.5 Pro':     {'input': 1.25,  'output': 10.00},
    'Gemini 2.5 Flash':   {'input': 0.15,  'output': 0.60},
    'Grok 3':             {'input': 3.00,  'output': 15.00},
    'Grok 3 mini':        {'input': 0.30,  'output': 0.50},
    'Llama 3 70B':        {'input': 0.59,  'output': 0.79},
    'Amazon Nova Pro':    {'input': 0.80,  'output': 3.20},
    'Amazon Nova Lite':   {'input': 0.06,  'output': 0.24},
}

TEST_PROMPT = "Write a Python function that reads a CSV file and returns the top 5 rows sorted by a given column name. Include error handling and type hints."


def model_size(name):
    """Extract numeric size from model name like qwen2.5-coder:14b -> 14."""
    m = re.search(r':(\d+\.?\d*)b', name)
    return float(m.group(1)) if m else 0


def cloud_cost_estimates(prompt_tokens, response_tokens):
    """Calculate cloud cost estimates for given token counts."""
    costs = []
    for name, price in CLOUD_PRICING.items():
        ci = prompt_tokens * price['input'] / 1_000_000
        co = response_tokens * price['output'] / 1_000_000
        costs.append({
            'provider': name,
            'input_cost': round(ci, 8),
            'output_cost': round(co, 8),
            'total_cost': round(ci + co, 8),
        })
    return costs
