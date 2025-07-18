from config.loader import ConfigLoader

import yaml
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class ModelManager:
    def __init__(self, root):
        self.root = root
        self.root.title("OCRacle")
        self.root.geometry("750x700")
        
        # Styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Colors
        bg_color = '#1e1e1e'  # Dark background
        fg_color = '#e0e0e0'  # Light text
        accent_color = '#64b5f6'  # Bright blue
        tab_bg = '#2d2d2d'  # Slightly lighter than background for tabs
        tab_fg = '#b0b0b0'  # Muted text for tabs
        
        # Configs
        self.style.configure('.', 
                           background=bg_color, 
                           foreground=fg_color, 
                           font=('Helvetica', 10))
                            
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TNotebook', background=bg_color, borderwidth=0, tabposition='n')
        
        self.style.layout('TNotebook', [
            ('Notebook.client', {'sticky': 'nswe'}),
            ('Notebook.tab', {'sticky': 'n'})
        ])
        
        self.style.configure('TNotebook.Tab', 
                           padding=[20, 6],
                           background=tab_bg,
                           foreground=tab_fg,
                           font=('Helvetica', 9))
                           
        self.style.map('TNotebook.Tab',
                     background=[('selected', bg_color), ('active', tab_bg)],
                     foreground=[('selected', accent_color), ('active', fg_color)])
        
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
        
        self.style.configure('TLabelframe', 
                           background=bg_color,
                           borderwidth=1,
                           relief='flat',
                           border='#333333')
                           
        self.style.configure('TLabelframe.Label',
                           font=('Helvetica', 16, 'bold'),
                           foreground=accent_color,
                           background=bg_color)
        
        self.style.configure('TCheckbutton',
                           background=bg_color,
                           foreground=fg_color,
                           font=('Helvetica', 12))
                           
        self.style.map('TCheckbutton',
                     background=[('active', '#2a2a2a')],
                     foreground=[('active', accent_color)])
        
        # Load configuration
        self.config_path = Path(__file__).parent / '../config/yaml/model_config.yaml'
        self.input_config_path = Path(__file__).parent / '../config/yaml/input_config.yaml'
        self.load_config()
        
        # Initialize input configuration variables
        self.dataset_path = tk.StringVar()
        self.images_count = tk.IntVar()
        self.load_input_config()
        
        # Create UI
        self.setup_ui()
    
    def load_config(self):
        """Load the model configuration from YAML file with validation."""
        try:
            loader = ConfigLoader()
            app_config = loader.load_app_config()
            
            # Convert back to dict format for compatibility with existing UI code
            self.config = {'models': []}
            for model in app_config.models_config.models:
                self.config['models'].append({
                    'provider': model.provider,
                    'id': model.id,
                    'enabled': model.enabled,
                    'api_key_env': model.api_key_env
                })
            
            # Group models by provider
            self.providers = {}
            for model in self.config.get('models', []):
                provider = model['provider']
                if provider not in self.providers:
                    self.providers[provider] = []
                self.providers[provider].append(model)
                
        except Exception as e:
            messagebox.showerror("Configuration Error", f"Failed to load configuration:\n{str(e)}")
            # Fallback to empty config
            self.config = {'models': []}
            self.providers = {}
    
    def load_input_config(self):
        """Load the input configuration from YAML file."""
        try:
            with open(self.input_config_path, 'r') as f:
                input_config = yaml.safe_load(f)
                if input_config and 'input' in input_config and input_config['input']:
                    first_input = input_config['input'][0]
                    self.dataset_path.set(first_input.get('path', ''))
                    self.images_count.set(first_input.get('images_to_process', 3))
                else:
                    self.dataset_path.set('')
                    self.images_count.set(3)
        except FileNotFoundError:
            # Set defaults if file doesn't exist
            self.dataset_path.set('')
            self.images_count.set(3)
        except Exception as e:
            messagebox.showerror("Input Config Error", f"Failed to load input configuration:\n{str(e)}")
            self.dataset_path.set('')
            self.images_count.set(3)

    def save_config(self):
        """Save both model and input configurations."""
        try:
            # Save model config
            models = []
            for provider_models in self.providers.values():
                models.extend(provider_models)
            
            self.config['models'] = models
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, sort_keys=False)
            
            # Save input config
            self.save_input_config()
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

    def save_input_config(self):
        """Save the input configuration to YAML file."""
        input_config = {
            'input': [{
                'path': self.dataset_path.get(),
                'images_to_process': self.images_count.get()
            }]
        }
        
        with open(self.input_config_path, 'w') as f:
            yaml.dump(input_config, f, sort_keys=False)

    def browse_dataset_folder(self):
        """Open file dialog to select dataset folder."""
        folder_path = filedialog.askdirectory(
            title="Select Folder",
            initialdir=self.dataset_path.get() if self.dataset_path.get() else "."
        )
        
        if folder_path:
            # Remove everything before "GT4HistOCR" from the path
            if "GT4HistOCR" in folder_path:
                # Find the position of GT4HistOCR and keep everything from there
                gt4hist_index = folder_path.find("GT4HistOCR")
                relative_path = folder_path[gt4hist_index:]
                self.dataset_path.set(relative_path)
            else:
                # If GT4HistOCR is not in the path, use the full path as fallback
                self.dataset_path.set(folder_path)
            
            # Check if folder contains PNG images and show count
            self.validate_dataset_folder(folder_path)

    def validate_dataset_folder(self, folder_path):
        """Validate the selected dataset folder and show image count."""
        try:
            path = Path(folder_path)
            png_files = list(path.glob("*.png"))
            
            if png_files:
                # Update the status label
                if hasattr(self, 'dataset_status_label'):
                    self.dataset_status_label.config(
                        text=f"✓ Found {len(png_files)} PNG images",
                        foreground='#81c784'
                    )
                # Suggest a reasonable default value for the images
                if len(png_files) < self.images_count.get():
                    self.images_count.set(min(len(png_files), 5))
            else:
                if hasattr(self, 'dataset_status_label'):
                    self.dataset_status_label.config(
                        text="⚠ No PNG images found",
                        foreground='#e57373'
                    )
        except Exception as e:
            if hasattr(self, 'dataset_status_label'):
                self.dataset_status_label.config(
                    text=f"✗ Error: {str(e)}",
                    foreground='#e57373'
                )
    
    def create_dataset_section(self, parent):
        """Create the dataset configuration section."""
        # Main dataset configuration frame
        dataset_frame = ttk.LabelFrame(
            parent,
            text=" Dataset and Models configuration ",
            padding=20,
            style='TLabelframe'
        )
        dataset_frame.pack(fill=tk.X, padx=0, pady=(20, 20))
        
        # Dataset path section
        path_section = ttk.Frame(dataset_frame)
        path_section.pack(fill=tk.X, pady=(0, 15))
        
        # Path label
        path_label = ttk.Label(
            path_section,
            text="Folder:",
            font=('Helvetica', 11, 'bold'),
            foreground='#e0e0e0'
        )
        path_label.pack(anchor='w', pady=(0, 5))
        
        # Path input frame
        path_input_frame = ttk.Frame(path_section)
        path_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Configure entry style
        self.style.configure('Dataset.TEntry',
                           fieldbackground='#2d2d2d',
                           foreground='#e0e0e0',
                           borderwidth=1,
                           insertcolor='#64b5f6')
        
        # Path entry
        path_entry = ttk.Entry(
            path_input_frame,
            textvariable=self.dataset_path,
            font=('Helvetica', 10),
            style='Dataset.TEntry',
            width=50
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Browse button
        browse_btn = ttk.Button(
            path_input_frame,
            text="Browse...",
            command=self.browse_dataset_folder,
            style='TButton',
            width=12
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Dataset status label
        self.dataset_status_label = ttk.Label(
            path_section,
            text="Select a folder containing PNG images",
            font=('Helvetica', 9),
            foreground='#b0b0b0'
        )
        self.dataset_status_label.pack(anchor='w')
        
        # Images count section
        count_section = ttk.Frame(dataset_frame)
        count_section.pack(fill=tk.X, pady=(10, 0))
        
        # Count label
        count_label = ttk.Label(
            count_section,
            text="Number of Images to Process:",
            font=('Helvetica', 11, 'bold'),
            foreground='#e0e0e0'
        )
        count_label.pack(anchor='w', pady=(0, 5))
        
        # Count input frame
        count_input_frame = ttk.Frame(count_section)
        count_input_frame.pack(anchor='w')
        
        # Configure spinbox style
        self.style.configure('Dataset.TSpinbox',
                           fieldbackground='#2d2d2d',
                           foreground='#e0e0e0',
                           borderwidth=1,
                           insertcolor='#64b5f6')
        
        # Images count spinbox
        count_spinbox = ttk.Spinbox(
            count_input_frame,
            from_=1,
            to=100,
            textvariable=self.images_count,
            font=('Helvetica', 10),
            style='Dataset.TSpinbox',
            width=10
        )
        count_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Count help text
        count_help = ttk.Label(
            count_input_frame,
            text="(Random selection from available images)",
            font=('Helvetica', 9),
            foreground='#b0b0b0'
        )
        count_help.pack(side=tk.LEFT)
        
        # Validate initial dataset if path exists
        if self.dataset_path.get():
            self.validate_dataset_folder(self.dataset_path.get())
    
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
        # Main container
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Dataset Configuration section
        self.create_dataset_section(main_frame)
        
        notebook_container = ttk.Frame(main_frame)
        notebook_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Notebook for model providers
        notebook = ttk.Notebook(notebook_container)
        notebook.pack(expand=True, pady=(0, 10))
        
        # Provider tabs
        for provider, models in sorted(self.providers.items()):
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=provider)
            
            frame = ttk.LabelFrame(
                tab, 
                text=f" {provider} ",
                padding=10,
                style='TLabelframe'
            )
            frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(15, 3))
            
            # Models checkboxes
            for model in models:
                var = tk.BooleanVar(value=model.get('enabled', False))
                var.trace_add('write', lambda *args, m=model, v=var: self.toggle_model(m, v))
                
                model_frame = ttk.Frame(frame)
                model_frame.pack(fill=tk.X, pady=2)
                
                cb = ttk.Checkbutton(
                    model_frame,
                    text=model['id'],
                    variable=var,
                    style='TCheckbutton',
                    padding=(5, 2)
                )
                cb.pack(side=tk.LEFT, anchor='w')
                
                # API key status
                api_key = model.get('api_key_env')
                has_api_key = bool(os.getenv(api_key)) if api_key else False
                
                status_text = "API Key: Configured" if has_api_key else "API Key: Required"
                status_color = '#81c784' if has_api_key else '#e57373'
                
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
        
        btn_frame = ttk.Frame(btn_container)
        btn_frame.pack(anchor='center')
        
        # Config primary button style
        self.style.configure('Primary.TButton',
                           background='#1976d2',
                           foreground='#ffffff',
                           font=('Helvetica', 9),
                           borderwidth=1,
                           padding=6)
                           
        self.style.map('Primary.TButton',
                     background=[('active', '#1565c0')],
                     foreground=[('active', '#ffffff')])
        
        # Save button
        btn_save = ttk.Button(
            btn_frame,
            text="Save Configuration",
            command=self.save_config,
            style='TButton',
            width=18
        )
        btn_save.pack(side=tk.LEFT, padx=6)
        
        # Run app button
        btn_run = ttk.Button(
            btn_frame,
            text="Run OCRacle",
            command=self.run_app,
            style='Primary.TButton',
            width=18
        )
        btn_run.pack(side=tk.LEFT, padx=6)
