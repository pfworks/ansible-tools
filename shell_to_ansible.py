#!/export/ollama/bin/python3
import sys
import ollama
import yaml

def generate_playbook(commands):
    prompt = f"""Convert these shell commands into an Ansible playbook. Return ONLY valid YAML, no explanations:

Commands:
{commands}

Generate a complete Ansible playbook with proper tasks."""

    response = ollama.chat(model='codellama:13b', messages=[
        {'role': 'user', 'content': prompt}
    ])
    
    return response['message']['content']

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ./shell_to_ansible.py <commands_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        commands = f.read()
    
    playbook = generate_playbook(commands)
    print(playbook)
