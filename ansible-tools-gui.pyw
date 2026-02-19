#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import urllib.request
import urllib.parse
import json
import os
import threading

class AnsibleToolsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ansible Tools")
        self.root.geometry("900x850")
        
        self.api_url = tk.StringVar(value=os.environ.get('ANSIBLE_TOOLS_API', 'http://localhost:5000'))
        self.model = tk.StringVar(value='codellama:13b')
        self.service = tk.StringVar(value='generate')
        
        self.create_widgets()
    
    def create_widgets(self):
        # Top frame - API URL, Model and Service selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="API URL:").pack(side=tk.LEFT, padx=5)
        api_entry = ttk.Entry(top_frame, textvariable=self.api_url, width=35)
        api_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top_frame, text="Model:").pack(side=tk.LEFT, padx=5)
        model_combo = ttk.Combobox(top_frame, textvariable=self.model, state='readonly', width=40)
        model_combo['values'] = (
            'codellama:7b (Fast, ~4GB RAM)',
            'codellama:13b (Balanced, ~8GB RAM)',
            'codellama:34b (Best Quality, ~20GB RAM)'
        )
        model_combo.current(1)
        model_combo.pack(side=tk.LEFT, padx=5)
        
        # Service selection
        service_frame = ttk.Frame(self.root, padding="10")
        service_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(service_frame, text="Shell → Ansible", variable=self.service, 
                       value='generate', command=self.switch_service).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(service_frame, text="Ansible → Explanation", variable=self.service,
                       value='explain', command=self.switch_service).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(service_frame, text="Description → Code", variable=self.service,
                       value='generate-code', command=self.switch_service).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(service_frame, text="Code → Explanation", variable=self.service,
                       value='explain-code', command=self.switch_service).pack(side=tk.LEFT, padx=10)
        
        # Input frame
        input_frame = ttk.LabelFrame(self.root, text="Input", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=15, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        input_buttons = ttk.Frame(input_frame)
        input_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(input_buttons, text="Upload File", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_buttons, text="Generate", command=self.generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_buttons, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.pack(fill=tk.X, padx=10)
        
        # Output frame
        output_frame = ttk.LabelFrame(self.root, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        output_buttons = ttk.Frame(output_frame)
        output_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(output_buttons, text="Copy", command=self.copy_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_buttons, text="Save", command=self.save_output).pack(side=tk.LEFT, padx=5)
    
    def switch_service(self):
        service = self.service.get()
        if service == 'generate':
            self.input_text.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)
            self.root.children['!labelframe'].config(text="Shell Commands")
            self.root.children['!labelframe2'].config(text="Ansible Playbook")
        elif service == 'explain':
            self.input_text.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)
            self.root.children['!labelframe'].config(text="Ansible Playbook")
            self.root.children['!labelframe2'].config(text="Explanation")
        elif service == 'generate-code':
            self.input_text.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)
            self.root.children['!labelframe'].config(text="Code Description")
            self.root.children['!labelframe2'].config(text="Generated Code")
        elif service == 'explain-code':
            self.input_text.delete(1.0, tk.END)
            self.output_text.delete(1.0, tk.END)
            self.root.children['!labelframe'].config(text="Code")
            self.root.children['!labelframe2'].config(text="Explanation")
    
    def upload_file(self):
        filename = filedialog.askopenfilename(
            title="Select file",
            filetypes=(("Text files", "*.txt"), ("Shell scripts", "*.sh"), 
                      ("YAML files", "*.yml *.yaml"), ("All files", "*.*"))
        )
        if filename:
            with open(filename, 'r') as f:
                content = f.read()
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(1.0, content)
    
    def get_model_value(self):
        model_str = self.model.get()
        if '7b' in model_str.lower():
            return 'codellama:7b'
        elif '34b' in model_str.lower():
            return 'codellama:34b'
        else:
            return 'codellama:13b'
    
    def generate(self):
        input_content = self.input_text.get(1.0, tk.END).strip()
        if not input_content:
            messagebox.showwarning("Warning", "Please enter some input")
            return
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._generate_thread, args=(input_content,))
        thread.daemon = True
        thread.start()
    
    def _generate_thread(self, input_content):
        try:
            api_url = self.api_url.get()
            
            # Check queue
            self.root.after(0, lambda: self.status_label.config(text="Checking queue..."))
            
            req = urllib.request.Request(f"{api_url}/queue-status")
            with urllib.request.urlopen(req) as response:
                queue_data = json.loads(response.read().decode())
            
            if queue_data.get('queue_size', 0) > 0:
                msg = f"Queue position: #{queue_data['queue_size'] + 1} - Generating..."
            else:
                msg = "Generating..."
            
            self.root.after(0, lambda: self.status_label.config(text=msg, foreground="blue"))
            
            # Make API call
            service = self.service.get()
            model = self.get_model_value()
            
            if service == 'generate':
                endpoint = '/generate'
                data = {'commands': input_content, 'model': model}
                output_key = 'playbook'
            elif service == 'explain':
                endpoint = '/explain'
                data = {'playbook': input_content, 'model': model}
                output_key = 'explanation'
            elif service == 'generate-code':
                endpoint = '/generate-code'
                data = {'description': input_content, 'model': model}
                output_key = 'code'
            else:  # explain-code
                endpoint = '/explain-code'
                data = {'code': input_content, 'model': model}
                output_key = 'explanation'
            
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{api_url}{endpoint}",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
            
            if result.get('error'):
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Error: {result['error']}", foreground="red"))
            else:
                output = result.get(output_key, '')
                self.root.after(0, lambda: self.output_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.output_text.insert(1.0, output))
                
                status_msg = f"Generated in {result['elapsed']}s | Tokens: {result['total_tokens']}"
                if result.get('queue_position'):
                    status_msg += f" | Was #{result['queue_position']} in queue"
                
                self.root.after(0, lambda: self.status_label.config(
                    text=status_msg, foreground="green"))
        
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(
                text=f"Error: {str(e)}", foreground="red"))
    
    def copy_output(self):
        output = self.output_text.get(1.0, tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_label.config(text="Copied to clipboard!", foreground="green")
    
    def save_output(self):
        output = self.output_text.get(1.0, tk.END).strip()
        if not output:
            messagebox.showwarning("Warning", "No output to save")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".yml",
            filetypes=(("YAML files", "*.yml"), ("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(output)
            self.status_label.config(text=f"Saved to {filename}", foreground="green")
    
    def clear_all(self):
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.status_label.config(text="")

if __name__ == '__main__':
    root = tk.Tk()
    app = AnsibleToolsGUI(root)
    root.mainloop()
