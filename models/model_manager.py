import yaml
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class ModelManager:
    def __init__(self, root):
        self.root = root
        self.root.title("OCRacle")
        self.root.geometry("700x350")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure colors - Dark theme
        bg_color = '#1e1e1e'  # Dark background
        fg_color = '#e0e0e0'  # Light text
        accent_color = '#64b5f6'  # Bright blue
        tab_bg = '#2d2d2d'  # Slightly lighter than background for tabs
        tab_fg = '#b0b0b0'  # Muted text for tabs
        
        # Configure styles
        self.style.configure('.', 
                           background=bg_color, 
                           foreground=fg_color, 
                           font=('Helvetica', 10))
                            
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TNotebook', background=bg_color, borderwidth=0)
        
        # Configure tabs
        self.style.configure('TNotebook.Tab', 
                           padding=[20, 6],
                           background=tab_bg,
                           foreground=tab_fg,
                           font=('Helvetica', 9))
                           
        self.style.map('TNotebook.Tab',
                     background=[('selected', bg_color), ('active', tab_bg)],
                     foreground=[('selected', accent_color), ('active', fg_color)])
        
        # Configure buttons
        self.style.configure('TButton', 
                           background='#2d2d2d',
                           foreground=fg_color,
                           borderwidth=1,
                           padding=6,
                           font=('Helvetica', 9))
                           
        self.style.map('TButton',
                     background=[('active', '#3d3d3d')],
                     foreground=[('active', accent_color)],
                     relief=[('active', 'flat')])
        
        # Configure label frames
        self.style.configure('TLabelframe', 
                           background=bg_color,
                           borderwidth=1,
                           relief='flat',
                           border='#333333')
                           
        self.style.configure('TLabelframe.Label',
                           font=('Helvetica', 16, 'bold'),
                           foreground=accent_color,
                           background=bg_color)
        
        # Configure checkbuttons with subtle hover effect
        self.style.configure('TCheckbutton',
                           background=bg_color,
                           foreground=fg_color,
                           font=('Helvetica', 12))
                           
        self.style.map('TCheckbutton',
                     background=[('active', '#2a2a2a')],
                     foreground=[('active', accent_color)])
        
        # Load configuration
        self.config_path = Path(__file__).parent / '../config/model_config.yaml'
        self.load_config()
        
        # Create UI
        self.setup_ui()
    
    def load_config(self):
        """Load the model configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Group models by provider
        self.providers = {}
        for model in self.config.get('models', []):
            provider = model['provider']
            if provider not in self.providers:
                self.providers[provider] = []
            self.providers[provider].append(model)
    
    def save_config(self):
        """Save the current configuration back to the YAML file."""
        # Rebuild the models list from providers
        models = []
        for provider_models in self.providers.values():
            models.extend(provider_models)
        
        # Update and save the config
        self.config['models'] = models
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, sort_keys=False)
        
        messagebox.showinfo("Success", "Configuration saved successfully!")
    
    def toggle_model(self, model, var):
        """Toggle a model's enabled state."""
        model['enabled'] = var.get()
        
    def run_app(self):
        """Run the main application."""
        import subprocess
        import sys
        import os
        
        # Save any pending changes first
        self.save_config()
        
        # Get the path to the current Python interpreter
        python = sys.executable
        app_path = os.path.join(os.path.dirname(__file__), '../run_process.py')
        
        try:
            # Run app.py in a new process
            subprocess.Popen([python, app_path])
            messagebox.showinfo("Success", "App is starting in a new window!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start app: {str(e)}")
    
    def setup_ui(self):
        # Create main container with subtle padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Create notebook for providers
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a tab for each provider
        for provider, models in sorted(self.providers.items()):
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=provider.capitalize())
            
            # Create a frame for the provider's models with clean styling
            frame = ttk.LabelFrame(
                tab, 
                text=f" {provider.capitalize()} ",
                padding=10,
                style='TLabelframe'
            )
            frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=3)
            
            # Add checkboxes for each model
            for model in models:
                var = tk.BooleanVar(value=model.get('enabled', False))
                var.trace_add('write', lambda *args, m=model, v=var: self.toggle_model(m, v))
                
                # Create a frame for each model
                model_frame = ttk.Frame(frame)
                model_frame.pack(fill=tk.X, pady=2)
                
                # Add checkbox
                cb = ttk.Checkbutton(
                    model_frame,
                    text=model['id'],
                    variable=var,
                    style='TCheckbutton',
                    padding=(5, 2)  # Add some padding around the text
                )
                cb.pack(side=tk.LEFT, anchor='w')
                
                # Add API key status with subtle styling
                api_key = model.get('api_key_env')
                has_api_key = bool(os.getenv(api_key)) if api_key else False
                
                status_text = "API Key: Configured" if has_api_key else "API Key: Required"
                status_color = '#81c784' if has_api_key else '#e57373'  # Softer green/red for dark theme
                
                status_label = ttk.Label(
                    model_frame,
                    text=status_text,
                    font=('Helvetica', 8),
                    foreground=status_color
                )
                status_label.pack(side=tk.LEFT, padx=10)
        
        # Add buttons container with subtle spacing
        btn_container = ttk.Frame(main_frame, padding=(0, 15, 0, 5))
        btn_container.pack(fill=tk.X)
        
        # Frame to center the buttons
        btn_frame = ttk.Frame(btn_container)
        btn_frame.pack(anchor='center')
        
        # Configure primary button style
        self.style.configure('Primary.TButton',
                           background='#1976d2',
                           foreground='#ffffff',
                           font=('Helvetica', 9),
                           borderwidth=1,
                           padding=6)
                           
        self.style.map('Primary.TButton',
                     background=[('active', '#1565c0')],
                     foreground=[('active', '#ffffff')])
        
        # Add save button
        btn_save = ttk.Button(
            btn_frame,
            text="Save Configuration",
            command=self.save_config,
            style='TButton',
            width=18
        )
        btn_save.pack(side=tk.LEFT, padx=6)
        
        # Add run app button
        btn_run = ttk.Button(
            btn_frame,
            text="Run OCRacle",
            command=self.run_app,
            style='Primary.TButton',
            width=18
        )
        btn_run.pack(side=tk.LEFT, padx=6)
