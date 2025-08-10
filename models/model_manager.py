from config.loader import ConfigLoader
from scripts.update_manifest import regenerate_full_manifest
from scripts.update_model_links import update_model_links
from utils.webserver.dashboard_ws import start_dashboard, open_dashboard, is_dashboard_running

import yaml
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from dotenv import load_dotenv
import os
from PIL import Image, ImageTk

load_dotenv()

PALETTE = {
    "BG_LIGHT": "#e9ecef",
    "BG_MEDIUM": "#f8f9fa",
    "TEXT_MAIN": "#2c3e50",
    "ACCENT": "#6c757d",
    "ACCENT_HOVER": "#495057",
    "TEXT_LIGHT": "#ffffff",
    "HIGHLIGHT": "#dc3545",
    "GREEN": "#28a745",
    "GOLDEN": "#d4af37",
    "GOLDEN_HOVER": "#b8860b",
    "DARK_BUTTON": "#343a40",
    "DARK_BUTTON_HOVER": "#6c757d",
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

class ModelManager:
    def __init__(self):
        self.root = ctk.CTk(fg_color=PALETTE["BG_LIGHT"])
        self.root.title("Palladia - Benchmark Manager")
        self.root.geometry("800x750")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configuration paths
        self.config_path = Path(__file__).parent / '../config/yaml/model_config.yaml'
        self.input_config_path = Path(__file__).parent / '../config/yaml/input_config.yaml'
        
        # Initialize variables
        self.dataset_path = ctk.StringVar()
        self.images_count = ctk.IntVar()
        self.prioritize_scanned = ctk.BooleanVar()
        
        # Process tracking
        self.running_process = None
        
        # Load configurations
        self.load_config()
        self.load_input_config()
        
        # Start dashboard server
        start_dashboard()
        
        # Create UI
        self.setup_ui()
    
    def load_config(self):
        """Load model configuration."""
        try:
            loader = ConfigLoader()
            app_config = loader.load_app_config()
            update_model_links() # Update links for dashboard on config loading
            
            self.config = {'models': []}
            for model in app_config.models_config.models:
                model_dict = {
                    'provider': model.provider,
                    'id': model.id,
                    'enabled': model.enabled,
                    'api_key_env': model.api_key_env
                }
                if model.standard_name:
                    model_dict['standard_name'] = model.standard_name
                if model.link:
                    model_dict['link'] = model.link
                self.config['models'].append(model_dict)
            
            # Group by provider
            self.providers = {}
            for model in self.config.get('models', []):
                provider = model['provider']
                if provider not in self.providers:
                    self.providers[provider] = []
                self.providers[provider].append(model)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.config = {'models': []}
            self.providers = {}
    
    def load_input_config(self):
        """Load input configuration."""
        try:
            with open(self.input_config_path, 'r') as f:
                input_config = yaml.safe_load(f)
                if input_config and 'input' in input_config and input_config['input']:
                    first_input = input_config['input'][0]
                    self.dataset_path.set(first_input.get('path', ''))
                    self.images_count.set(first_input.get('images_to_process', 3))
                    self.prioritize_scanned.set(first_input.get('prioritize_scanned', False))
                else:
                    self._set_defaults()
        except FileNotFoundError:
            self._set_defaults()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load input config: {e}")
            self._set_defaults()
    
    def _set_defaults(self):
        """Set default values."""
        self.dataset_path.set('')
        self.images_count.set(3)
        self.prioritize_scanned.set(False)

    def save_config(self):
        """Save configurations."""
        try:
            # Save model config
            models = []
            for provider_models in self.providers.values():
                models.extend(provider_models)
            
            self.config['models'] = models
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, sort_keys=False)
            
            # Save input config
            input_config = {
                'input': [{
                    'path': self.dataset_path.get(),
                    'images_to_process': self.images_count.get(),
                    'prioritize_scanned': self.prioritize_scanned.get()
                }]
            }
            with open(self.input_config_path, 'w') as f:
                yaml.dump(input_config, f, sort_keys=False)
            
            messagebox.showinfo("Success", "Configuration saved!")
            self.update_status_bar()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def browse_dataset_folder(self):
        """Select dataset folder."""
        folder_path = filedialog.askdirectory(
            title="Select Dataset Folder",
            initialdir=self.dataset_path.get() if self.dataset_path.get() else "."
        )
        
        if folder_path:
            if "GT4HistOCR" in folder_path:
                gt4hist_index = folder_path.find("GT4HistOCR")
                relative_path = folder_path[gt4hist_index:]
                self.dataset_path.set(relative_path)
            else:
                self.dataset_path.set(folder_path)
            
            self.validate_dataset_folder(folder_path)

    def validate_dataset_folder(self, folder_path):
        """Validate dataset folder."""
        try:
            path = Path(folder_path)
            png_files = list(path.glob("*.png"))
            
            if hasattr(self, 'dataset_status_label'):
                if png_files:
                    self.dataset_status_label.configure(
                        text=f"Found {len(png_files)} PNG images", 
                        text_color="green",
                        font=ctk.CTkFont(weight="bold")
                    )
                    if len(png_files) < self.images_count.get():
                        self.images_count.set(min(len(png_files), 5))
                else:
                    self.dataset_status_label.configure(text="No PNG images found", text_color="red")
        except Exception as e:
            if hasattr(self, 'dataset_status_label'):
                self.dataset_status_label.configure(text=f"Error: {e}", text_color="red")
    
    def update_selection_help_text(self):
        """Update help text."""
        if hasattr(self, 'count_help'):
            if self.prioritize_scanned.get():
                self.count_help.configure(text="(Prioritizes scanned images first)")
            else:
                self.count_help.configure(text="(Random selection)")
    
    def create_dataset_section(self, parent):
        """Create dataset configuration section."""
        dataset_frame = ctk.CTkFrame(parent, fg_color=PALETTE["BG_MEDIUM"])
        dataset_frame.pack(fill="x", pady=(15, 15), padx=18)
        
        # Title
        title_label = ctk.CTkLabel(dataset_frame, text="Dataset Configuration", 
                                  font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=(12, 10))
        
        # Path selection
        path_label = ctk.CTkLabel(dataset_frame, text="Dataset Folder:")
        path_label.pack(anchor="w", padx=18, pady=(8, 5))
        
        path_frame = ctk.CTkFrame(dataset_frame, fg_color=PALETTE["BG_MEDIUM"])
        path_frame.pack(fill="x", padx=18, pady=(0, 10))
        
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.dataset_path, 
                                      placeholder_text="Select dataset folder...")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=8)
        
        browse_btn = ctk.CTkButton(path_frame, text="Browse", command=self.browse_dataset_folder, width=80, height=28, fg_color=PALETTE["DARK_BUTTON"], hover_color=PALETTE["DARK_BUTTON_HOVER"], text_color=PALETTE["TEXT_LIGHT"])
        browse_btn.pack(side="right", padx=(8, 10), pady=8)
        
        self.dataset_status_label = ctk.CTkLabel(dataset_frame, text="Select a folder with PNG images")
        self.dataset_status_label.pack(anchor="w", padx=18, pady=(0, 10))
        
        # Image count
        count_label = ctk.CTkLabel(dataset_frame, text="Images to Process:")
        count_label.pack(anchor="w", padx=18, pady=(8, 5))
        
        count_input_frame = ctk.CTkFrame(dataset_frame, fg_color=PALETTE["BG_MEDIUM"])
        count_input_frame.pack(fill="x", padx=18, pady=(0, 15))
        
        # Simple entry field for number input
        count_entry = ctk.CTkEntry(count_input_frame, textvariable=self.images_count, width=60, height=28)
        count_entry.pack(side="left", padx=(10, 8), pady=8)
                
        self.count_help = ctk.CTkLabel(count_input_frame, text="(Prioritizes scanned images first)" if self.prioritize_scanned.get() else "(Random selection)", text_color="grey", font=ctk.CTkFont(size=12))
        self.count_help.pack(side="left", padx=(0, 10), pady=8)
        
        # Priority option on the right
        self.priority_checkbox = ctk.CTkCheckBox(
            count_input_frame,
            text="Prioritize already scanned images",
            variable=self.prioritize_scanned,
            command=self.update_selection_help_text,
            fg_color=PALETTE["GOLDEN"],              # Unchecked background
            hover_color=PALETTE["GOLDEN_HOVER"],     # Hover color
            checkmark_color=PALETTE["BG_LIGHT"],     # Checkmark color
            border_color=PALETTE["GOLDEN"]           # Border color
        )
        self.priority_checkbox.pack(side="right", padx=(10, 15), pady=8)
        
        # Validate initial path
        if self.dataset_path.get():
            self.validate_dataset_folder(self.dataset_path.get())
    
    def check_process_status(self):
        """Check if the Palladia process is still running."""
        if self.running_process:
            if self.running_process.poll() is None:
                # Process is still running, check again in 1 second
                self.root.after(1000, self.check_process_status)
            else:
                # Process has finished
                self.running_process = None
                if hasattr(self, 'run_btn'):
                    self.run_btn.configure(text="Run Palladia", state="normal")
                    self.status_word_label.configure(text="Ready", text_color="green")
                messagebox.showinfo("Complete", "Palladia process has finished!")
    
    def on_tab_change(self):
        """Handle tab change to update status bar."""
        self.update_status_bar()
    
    def toggle_model(self, model, var):
        """Toggle model enabled state."""
        model['enabled'] = var.get()
        self.update_status_bar()
        
    def run_app(self):
        """Run main application."""
        import subprocess
        import sys
        import os
        
        # Check if process is already running
        if self.running_process and self.running_process.poll() is None:
            messagebox.showwarning("Warning", "Palladia is already running!")
            return
        
        self.save_config()
        
        python = sys.executable
        app_path = os.path.join(os.path.dirname(__file__), '../scripts/run_process.py')
        
        try:
            self.running_process = subprocess.Popen([python, app_path])
            messagebox.showinfo("Success", "Palladia is starting!")
            
            # Disable the button and start checking process status
            if hasattr(self, 'run_btn'):
                self.run_btn.configure(text="Palladia Running...", state="disabled")
                self.status_word_label.configure(text="Running", text_color="orange")
            
            # Start periodic check
            self.check_process_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start app: {e}")
            self.running_process = None
    
    def open_dashboard(self):
        """Open dashboard in browser."""
        try:
            open_dashboard()
            messagebox.showinfo("Dashboard", "Opening in browser!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open dashboard: {e}")
    
    def setup_ui(self):
        """Create the UI."""
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color=PALETTE["BG_LIGHT"])
        main_frame.pack(fill="both", expand=True, padx=8, pady=5)
        
        # Dataset section
        self.create_dataset_section(main_frame)
        
        # Models section
        models_frame = ctk.CTkFrame(main_frame, fg_color=PALETTE["BG_MEDIUM"])
        models_frame.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        
        models_title = ctk.CTkLabel(models_frame, text="Model Selection", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        models_title.pack(pady=(8, 5))
        
        # Provider tabs
        self.tabview = ctk.CTkTabview(models_frame, fg_color=PALETTE["BG_MEDIUM"], 
                                     command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        
        self.tabview._segmented_button.configure(
            fg_color=PALETTE["ACCENT"],              # Background of tab bar
            selected_color=PALETTE["GOLDEN"],        # Selected tab color
            selected_hover_color=PALETTE["GOLDEN_HOVER"],  # Selected tab hover
            unselected_color=PALETTE["ACCENT"],      # Unselected tab color
            unselected_hover_color=PALETTE["ACCENT_HOVER"],   # Unselected tab hover
            text_color=PALETTE["TEXT_LIGHT"],        # Text color for unselected tabs
            text_color_disabled=PALETTE["TEXT_MAIN"] # Text color for selected tabs
        )
        
        self.model_vars = {}
        
        for provider, models in sorted(self.providers.items()):
            # Check if all models in this provider have API keys
            all_have_keys = True
            for model in models:
                api_key = model.get('api_key_env')
                has_api_key = bool(os.getenv(api_key)) if api_key else False
                if not has_api_key:
                    all_have_keys = False
                    break
            
            # API key availability symbol
            if all_have_keys:
                tab_name = f"● {provider}"
            else:
                tab_name = f"○ {provider}"
            
            tab = self.tabview.add(tab_name)
            
            # Scrollable frame for model list
            scrollable_frame = ctk.CTkScrollableFrame(tab, fg_color=PALETTE["BG_LIGHT"])
            scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            for model in models:
                api_key = model.get('api_key_env')
                has_api_key = bool(os.getenv(api_key)) if api_key else False
                
                # If no API key, disable the model
                if not has_api_key:
                    model['enabled'] = False
                
                var = ctk.BooleanVar(value=model.get('enabled', False) if has_api_key else False)
                var.trace_add('write', lambda *args, m=model, v=var: self.toggle_model(m, v))
                self.model_vars[model['id']] = var
                
                model_frame = ctk.CTkFrame(scrollable_frame, fg_color=PALETTE["BG_LIGHT"])
                model_frame.pack(fill="x", pady=3, padx=8)
                
                checkbox = ctk.CTkCheckBox(
                    model_frame, 
                    text=model['id'], 
                    variable=var,
                    state="disabled" if not has_api_key else "normal",
                    fg_color=PALETTE["GOLDEN"],              # Unchecked background (golden)
                    hover_color=PALETTE["GOLDEN_HOVER"],     # Hover color (darker golden)
                    checkmark_color=PALETTE["TEXT_LIGHT"],   # Checkmark color (white)
                    border_color=PALETTE["GOLDEN"]           # Border color (golden)
                )
                checkbox.pack(side="left", padx=10, pady=6)
        
        # Status bar
        self.create_status_bar()
        self.update_status_bar()
        
        # Create static button bar
        self.create_button_bar()
    
    def create_button_bar(self):
        """Create static button bar."""
        btn_frame = ctk.CTkFrame(self.root, fg_color=PALETTE["BG_LIGHT"])
        btn_frame.pack(fill="x", side="bottom", padx=8, pady=(0, 5))
        
        center_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        center_frame.pack(pady=6)
        
        manifest_btn = ctk.CTkButton(center_frame, text="Update Manifest", 
                                    command=regenerate_full_manifest, width=120, height=32, fg_color=PALETTE["DARK_BUTTON"], hover_color=PALETTE["DARK_BUTTON_HOVER"], text_color=PALETTE["TEXT_LIGHT"])
        manifest_btn.pack(side="left", padx=8)
        
        save_btn = ctk.CTkButton(center_frame, text="Save Config", 
                                command=self.save_config, width=120, height=32, fg_color=PALETTE["DARK_BUTTON"], hover_color=PALETTE["DARK_BUTTON_HOVER"], text_color=PALETTE["TEXT_LIGHT"])
        save_btn.pack(side="left", padx=8)
        
        self.dashboard_btn = ctk.CTkButton(center_frame, text="Open Dashboard", 
                                          command=self.open_dashboard, width=120, height=32, fg_color=PALETTE["DARK_BUTTON"], hover_color=PALETTE["DARK_BUTTON_HOVER"], text_color=PALETTE["TEXT_LIGHT"])
        self.dashboard_btn.pack(side="left", padx=8)
        
        self.run_btn = ctk.CTkButton(center_frame, text="Run Palladia", 
                               command=self.run_app, width=120, height=32,
                               fg_color="green", hover_color="darkgreen")
        self.run_btn.pack(side="left", padx=8)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_frame = ctk.CTkFrame(self.root, fg_color=PALETTE["BG_MEDIUM"], corner_radius=0)
        self.status_frame.pack(fill="x", side="bottom", padx=0, pady=(5, 0))
        
        # Left side frame for status text
        left_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=12, pady=5)
        
        # Separate labels for status and details
        self.status_word_label = ctk.CTkLabel(left_frame, text="Ready", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.status_word_label.pack(side="left")
        
        self.status_details_label = ctk.CTkLabel(left_frame, text="")
        self.status_details_label.pack(side="left")
        
        # Right side frame for logo and version info
        right_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=12, pady=5)

        try:
            logo_path = Path(__file__).parent / '../docs/images/dashboard/palladia.png'
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                self.logo_photo = ctk.CTkImage(logo_image, size=(32, 32))
                
                logo_label = ctk.CTkLabel(right_frame, image=self.logo_photo, text="")
                logo_label.pack(side="left", padx=(0, 5))
        except Exception:
            pass
        
        self.info_label = ctk.CTkLabel(right_frame, text="Palladia v1.0")
        self.info_label.pack(side="left")
    
    def update_status_bar(self):
        """Update status bar."""
        try:
            enabled_models = sum(
                sum(1 for model in models if model.get('enabled', False))
                for models in self.providers.values()
            )
            total_models = sum(len(models) for models in self.providers.values())
            
            # Check current selected tab for API key status
            current_tab = None
            current_provider = None
            status_message = "Ready"
            status_color = "green"
            
            try:
                current_tab = self.tabview.get()
                if current_tab:
                    # Temporarily remove the dot indicator to get the provider name
                    current_provider = current_tab.replace("● ", "").replace("○ ", "")
                    
                    # Check if current provider has all API keys
                    if current_provider in self.providers:
                        provider_models = self.providers[current_provider]
                        missing_api_keys = False
                        
                        for model in provider_models:
                            api_key = model.get('api_key_env')
                            has_api_key = bool(os.getenv(api_key)) if api_key else False
                            if not has_api_key:
                                missing_api_keys = True
                                break
                        
                        if missing_api_keys:
                            status_message = "API Key Required"
                            status_color = "red"
                        else:
                            status_message = "Ready"
                            status_color = "green"
            except:
                status_message = "Error"
                status_color = "red"
            
            # Status details
            if enabled_models > 0:
                status_details = f" | {enabled_models}/{total_models} models selected"
            else:
                status_details = f" | No models selected"
            
            # Update status labels separately
            self.status_word_label.configure(text=status_message, text_color=status_color)
            self.status_details_label.configure(text=status_details)
            self.info_label.configure(text=f"Palladia v1.0")
            
        except Exception:
            self.status_word_label.configure(text="Status error", text_color="red")
            self.status_details_label.configure(text="")
            self.info_label.configure(text="Palladia v1.0")
    
    def on_closing(self):
        """Handle app closing."""
        from utils.webserver.dashboard_ws import stop_dashboard
        try:
            stop_dashboard()
        except:
            pass
        
        # Clean up running process if it exists
        if self.running_process and self.running_process.poll() is None:
            try:
                self.running_process.terminate()
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
