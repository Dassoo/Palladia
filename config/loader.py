import yaml
from pathlib import Path
from typing import Optional
from pydantic import ValidationError
from rich.console import Console
from rich.text import Text

from .schemas import ModelsConfig, InputConfig, AppConfig

console = Console()


class ConfigLoader:
    """Handles loading and validation of application configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.models_config_path = self.config_dir / "yaml" / "model_config.yaml"
        self.input_config_path = self.config_dir / "yaml" / "input_config.yaml"
    
    def load_models_config(self) -> ModelsConfig:
        """Load and validate models configuration."""
        try:
            with open(self.models_config_path, 'r') as f:
                data = yaml.safe_load(f)
            return ModelsConfig(**data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Models config not found: {self.models_config_path}")
        except ValidationError as e:
            console.print(Text("❌ Models configuration validation failed:", style="bold red"))
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                console.print(Text(f"  {field}: {error['msg']}", style="red"))
            raise
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in models config: {e}")
    
    def load_input_config(self) -> InputConfig:
        """Load and validate input configuration."""
        try:
            with open(self.input_config_path, 'r') as f:
                data = yaml.safe_load(f)
            return InputConfig(**data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Input config not found: {self.input_config_path}")
        except ValidationError as e:
            console.print(Text("❌ Input configuration validation failed:", style="bold red"))
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                console.print(Text(f"  {field}: {error['msg']}", style="red"))
            raise
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in input config: {e}")
    
    def load_app_config(self, verbose: bool = True) -> AppConfig:
        """Load and validate complete application configuration."""
        models_config = self.load_models_config()
        input_config = self.load_input_config()
        
        app_config = AppConfig(
            models_config=models_config,
            input_config=input_config
        )
        
        # Print helpful warnings
        self._print_config_warnings(app_config, verbose)
        
        return app_config
    
    def _print_config_warnings(self, config: AppConfig, verbose: bool = True):
        """Print helpful warnings about configuration."""
        if not verbose:
            return
            
        # Warn about missing API keys
        missing_keys = config.missing_api_keys
        if missing_keys:
            console.print(Text("Missing API keys for enabled models:", style="bold yellow"))
            for missing in missing_keys:
                console.print(Text(f"  • {missing}", style="yellow"))
            console.print()
        
        # Info about enabled models
        enabled = config.enabled_models
        if enabled:
            console.print(Text(f"{len(enabled)} model(s) enabled for benchmark:", style="bold green"))
            for model in enabled:
                display_name = model.display_name
                if display_name != model.id:
                    console.print(Text(f"  • {model.provider}/{display_name} (ID: {model.id})", style="green"))
                else:
                    console.print(Text(f"  • {model.provider}/{model.id}", style="green"))
        else:
            console.print(Text("No models enabled for evaluation", style="bold yellow"))
        
        console.print()


# Convenience function for easy importing
def load_config(verbose: bool = True) -> AppConfig:
    """Load and validate application configuration."""
    loader = ConfigLoader()
    return loader.load_app_config(verbose=verbose)