from config.loader import ConfigLoader
from utils.update_manifest import regenerate_full_manifest
from utils.webserver.dashboard_ws import start_dashboard, is_dashboard_running

import yaml
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class ModelManager:
    def __init__(self, root):
        self.root = root
        self.root.title("OCRacle - Model Manager")
        self.root.geometry("900x820")
        self.root.configure(bg='#555879')
        
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.title_font = tkFont.Font(family="Segoe UI", size=12, weight="bold")
        self.header_font = tkFont.Font(family="Segoe UI", size=10, weight="bold")
        self.body_font = tkFont.Font(family="Segoe UI", size=9)
        self.small_font = tkFont.Font(family="Segoe UI", size=8)
        
        # Styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Color scheme - matching web dashboard
        bg_color = '#555879'  # Dark background
        fg_color = '#F4EBD3'  # Cream text
        accent_color = '#F4EBD3'  # Cream accent
        tab_bg = '#555879'  # Dark tabs
        tab_fg = '#F4EBD3'  # Dark text for tabs
        container_bg = '#555879'  # Container background
        
        status_bg = '#1A1A1A'  # Status bar background
        button_primary = '#555879'  # Primary button color
        button_secondary = '#98A1BC'  # Secondary button color
        
        # Configure styles with modern fonts
        self.style.configure('.', 
                           background=bg_color, 
                           foreground=fg_color, 
                           font=self.body_font)
                            
        self.style.configure('TFrame', background=bg_color)
        
        # Container styles
        self.style.configure('Container.TFrame', 
                           background=container_bg,
                           relief='solid',
                           borderwidth=0,
                           bordercolor=accent_color)
        
        self.style.configure('TNotebook', 
                           background=bg_color, 
                           borderwidth=1, 
                           tabposition='n',
                           bordercolor=accent_color)
        
        self.style.layout('TNotebook', [
            ('Notebook.client', {'sticky': 'nswe'}),
            ('Notebook.tab', {'sticky': 'n'})
        ])
        
        self.style.configure('TNotebook.Tab', 
                           padding=[20, 10],
                           background=tab_bg,
                           foreground=tab_fg,
                           font=self.body_font,
                           borderwidth=1)
                           
        self.style.map('TNotebook.Tab',
                     background=[('selected', '#37394f'), ('active', '#E8DCC6')],
                     foreground=[('selected', accent_color), ('active', '#37394f')])
        
        self.style.configure('TButton', 
                           background=button_secondary,
                           foreground='#F4EBD3',
                           borderwidth=1,
                           padding=10,
                           font=self.body_font,
                           bordercolor=button_secondary)
                           
        self.style.map('TButton',
                     background=[('active', '#7A8399')],
                     foreground=[('active', '#F4EBD3')],
                     relief=[('active', 'flat')])
        
        self.style.configure('TLabelframe', 
                           background=bg_color,
                           borderwidth=2,
                           relief='solid',
                           bordercolor='#98A1BC')
                           
        self.style.configure('TLabelframe.Label',
                           font=self.header_font,
                           foreground=accent_color,
                           background=bg_color)
        
        self.style.configure('TCheckbutton',
                           background=bg_color,
                           foreground=fg_color,
                           font=self.body_font,
                           focuscolor='none')
                           
        self.style.map('TCheckbutton',
                     background=[('active', '#E8DCC6')],
                     foreground=[('active', '#37394f')])
        
        # Status bar style
        self.style.configure('Status.TFrame',
                           background=status_bg,
                           relief='solid',
                           borderwidth=1,
                           bordercolor='#98A1BC')
        
        # Load configuration
        self.config_path = Path(__file__).parent / '../config/yaml/model_config.yaml'
        self.input_config_path = Path(__file__).parent / '../config/yaml/input_config.yaml'
        self.load_config()
        
        # Initialize input configuration variables
        self.dataset_path = tk.StringVar()
        self.images_count = tk.IntVar()
        self.prioritize_scanned = tk.BooleanVar()
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
                model_dict = {
                    'provider': model.provider,
                    'id': model.id,
                    'enabled': model.enabled,
                    'api_key_env': model.api_key_env
                }
                # Preserve optional fields if they exist
                if model.standard_name:
                    model_dict['standard_name'] = model.standard_name
                if model.link:
                    model_dict['link'] = model.link
                self.config['models'].append(model_dict)
            
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
                    self.prioritize_scanned.set(first_input.get('prioritize_scanned', False))
                else:
                    self.dataset_path.set('')
                    self.images_count.set(3)
                    self.prioritize_scanned.set(False)
        except FileNotFoundError:
            # Set defaults if file doesn't exist
            self.dataset_path.set('')
            self.images_count.set(3)
            self.prioritize_scanned.set(False)
        except Exception as e:
            messagebox.showerror("Input Config Error", f"Failed to load input configuration:\n{str(e)}")
            self.dataset_path.set('')
            self.images_count.set(3)
            self.prioritize_scanned.set(False)

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
                'images_to_process': self.images_count.get(),
                'prioritize_scanned': self.prioritize_scanned.get()
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
    
    def update_selection_help_text(self):
        """Update the help text based on prioritization setting."""
        if hasattr(self, 'count_help'):
            if self.prioritize_scanned.get():
                self.count_help.config(text="(Prioritizes scanned images, then random)")
            else:
                self.count_help.config(text="(Random selection from available images)")
    
    def create_dataset_section(self, parent):
        """Create the dataset configuration section."""
        # Main dataset configuration container
        dataset_container = ttk.Frame(parent, style='Container.TFrame', padding=15)
        dataset_container.pack(fill=tk.X, pady=(0, 15))
        
        # Dataset configuration frame
        dataset_frame = ttk.LabelFrame(
            dataset_container,
            text=" Dataset Configuration ",
            padding=20,
            style='TLabelframe'
        )
        dataset_frame.pack(fill=tk.X)
        
        # Dataset path section
        path_section = ttk.Frame(dataset_frame)
        path_section.pack(fill=tk.X, pady=(0, 15))
        
        # Path label
        path_label = ttk.Label(
            path_section,
            text="Folder:",
            font=self.header_font,
            foreground='#F4EBD3'
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
            font=self.body_font,
            style='Dataset.TEntry',
            width=50
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Browse button
        browse_btn = ttk.Button(
            path_input_frame,
            text="Browse Folder...",
            command=self.browse_dataset_folder,
            style='TButton',
            width=15
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Dataset status label
        self.dataset_status_label = ttk.Label(
            path_section,
            text="Select a folder containing PNG images",
            font=self.small_font,
            foreground='#98A1BC'
        )
        self.dataset_status_label.pack(anchor='w')
        
        # Images count section
        count_section = ttk.Frame(dataset_frame)
        count_section.pack(fill=tk.X, pady=(10, 0))
        
        # Count label
        count_label = ttk.Label(
            count_section,
            text="Number of Images to Process:",
            font=self.header_font,
            foreground='#F4EBD3'
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
            font=self.body_font,
            style='Dataset.TSpinbox',
            width=10
        )
        count_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Count help text
        self.count_help = ttk.Label(
            count_input_frame,
            text="(Random selection from available images)",
            font=self.small_font,
            foreground='#b0b0b0'
        )
        self.count_help.pack(side=tk.LEFT)
        
        # Prioritization section
        priority_section = ttk.Frame(dataset_frame)
        priority_section.pack(fill=tk.X, pady=(15, 0))
        
        # Priority checkbox
        priority_checkbox = ttk.Checkbutton(
            priority_section,
            text="Prioritize images that have already been scanned",
            variable=self.prioritize_scanned,
            style='TCheckbutton',
            command=self.update_selection_help_text
        )
        priority_checkbox.pack(anchor='w')
        
        # Priority help text
        priority_help = ttk.Label(
            priority_section,
            text="When enabled, images with existing JSON results will be selected first, then random images",
            font=self.small_font,
            foreground='#b0b0b0'
        )
        priority_help.pack(anchor='w', pady=(2, 0))
        
        # Validate initial dataset if path exists
        if self.dataset_path.get():
            self.validate_dataset_folder(self.dataset_path.get())
    
    def toggle_model(self, model, var):
        """Toggle a model's enabled state."""
        model['enabled'] = var.get()
        # Update status bar when model selection changes
        self.update_status_bar()
        
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
    
    def open_dashboard(self):
        """Open the dashboard in browser."""
        try:
            start_dashboard()
            # Update button text to reflect dashboard status
            if hasattr(self, 'dashboard_btn'):
                self.dashboard_btn.config(text="Dashboard Running")
            messagebox.showinfo("Dashboard", "Dashboard is opening in your browser!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start dashboard: {str(e)}")
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Dataset Configuration section
        self.create_dataset_section(main_frame)
        
        # Model Selection Container
        models_container = ttk.Frame(main_frame, style='Container.TFrame', padding=15)
        models_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Models header
        models_header = ttk.LabelFrame(
            models_container,
            text=" Models Selection ",
            padding=(15, 10),
            style='TLabelframe'
        )
        models_header.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for model providers
        notebook = ttk.Notebook(models_header)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Provider tabs
        for provider, models in sorted(self.providers.items()):
            tab = ttk.Frame(notebook, padding=15)
            notebook.add(tab, text=f"{provider}")
            
            # Models list frame
            models_frame = ttk.Frame(tab)
            models_frame.pack(fill=tk.BOTH, expand=True)
            
            # Models checkboxes
            for model in models:
                var = tk.BooleanVar(value=model.get('enabled', False))
                var.trace_add('write', lambda *args, m=model, v=var: self.toggle_model(m, v))
                
                model_frame = ttk.Frame(models_frame)
                model_frame.pack(fill=tk.X, pady=3)
                
                cb = ttk.Checkbutton(
                    model_frame,
                    text=model['id'],
                    variable=var,
                    style='TCheckbutton',
                    padding=(5, 4)
                )
                cb.pack(side=tk.LEFT, anchor='w')
                
                # API key status
                api_key = model.get('api_key_env')
                has_api_key = bool(os.getenv(api_key)) if api_key else False
                
                status_text = "API Key set" if has_api_key else "API Key required"
                status_color = '#81c784' if has_api_key else '#e57373'
                
                status_label = ttk.Label(
                    model_frame,
                    text=status_text,
                    font=self.small_font,
                    foreground=status_color
                )
                status_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Add buttons container with subtle spacing
        btn_container = ttk.Frame(main_frame, padding=(0, 15, 0, 5))
        btn_container.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(btn_container)
        btn_frame.pack(anchor='center')
        
        # Config primary button style
        self.style.configure('Primary.TButton',
                           background='#37394f',
                           foreground='#F4EBD3',
                           font=self.body_font,
                           borderwidth=1,
                           padding=8)
                           
        self.style.map('Primary.TButton',
                     background=[('active', '#252636')],
                     foreground=[('active', '#F4EBD3')])
        
        # Config dashboard button style
        self.style.configure('Dash.TButton',
                           background='#F4EBD3',
                           foreground='#1A1A1A',
                           font=self.body_font,
                           borderwidth=1,
                           padding=8)
                           
        self.style.map('Dash.TButton',
                     background=[('active', '#b3ac9a')],
                     foreground=[('active', '#1A1A1A')])
        
        # Manifest refresh button
        btn_manifest = ttk.Button(
            btn_frame,
            text="Update Manifest",
            command=regenerate_full_manifest,
            style='TButton',
            width=18
        )
        btn_manifest.pack(side=tk.LEFT, padx=8)
        
        # Save button
        btn_save = ttk.Button(
            btn_frame,
            text="Save Config",
            command=self.save_config,
            style='TButton',
            width=12
        )
        btn_save.pack(side=tk.LEFT, padx=8)
        
        # Dashboard button
        dashboard_text = "Dashboard Running..." if is_dashboard_running() else "Open Dashboard"
        self.dashboard_btn = ttk.Button(
            btn_frame,
            text=dashboard_text,
            command=self.open_dashboard,
            style='Dash.TButton',
            width=18
        )
        self.dashboard_btn.pack(side=tk.LEFT, padx=8)
        
        # Run app button
        btn_run = ttk.Button(
            btn_frame,
            text="Run OCRacle",
            command=self.run_app,
            style='Primary.TButton',
            width=18
        )
        btn_run.pack(side=tk.LEFT, padx=8)
        
        # Status bar
        self.create_status_bar()
        
        # Update status bar with initial information
        self.update_status_bar()
    
    def create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_bar = ttk.Frame(self.root, style='Status.TFrame', padding=(10, 5))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Left side - Status message
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            font=self.small_font,
            foreground='#b0b0b0',
            background='#1a1a1a'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Right side - Model and dataset info
        self.info_label = ttk.Label(
            self.status_bar,
            text="OCRacle v1.0",
            font=self.small_font,
            foreground='#F4EBD3',
            background='#1a1a1a'
        )
        self.info_label.pack(side=tk.RIGHT)
    
    def update_status_bar(self):
        """Update the status bar with current configuration information."""
        try:
            # Count enabled models
            enabled_models = sum(
                sum(1 for model in models if model.get('enabled', False))
                for models in self.providers.values()
            )
            total_models = sum(len(models) for models in self.providers.values())
            
            # Get dataset info
            dataset_info = ""
            if self.dataset_path.get():
                try:
                    path = Path(self.dataset_path.get())
                    if path.exists():
                        png_files = list(path.glob("*.png"))
                        dataset_info = f" • Dataset: {len(png_files)} images"
                    else:
                        dataset_info = " • Dataset: Path not found"
                except:
                    dataset_info = " • Dataset: Error reading path"
            else:
                dataset_info = " • Dataset: Not selected"
            
            # Update status
            if enabled_models > 0:
                status_text = f"Ready • {enabled_models}/{total_models} models selected"
            else:
                status_text = "No models selected"
            
            self.status_label.config(text=status_text)
            
            # Update info
            info_text = f"OCRacle v1.0{dataset_info}"
            self.info_label.config(text=info_text)
            
        except Exception as e:
            self.status_label.config(text="Status update error")
            self.info_label.config(text="OCRacle v1.0")
    
    def on_closing(self):
        """Handle application closing and cleanup dashboard server."""
        from utils.webserver.dashboard_ws import stop_dashboard
        try:
            stop_dashboard()
        except:
            pass
        self.root.destroy()