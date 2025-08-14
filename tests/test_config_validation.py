import tempfile
import yaml
import pytest
from pathlib import Path

from config.loader import ConfigLoader
from config.schemas import ModelsConfig, InputConfig

def test_valid_config():
    """Test with a valid configuration."""
    
    # Create temporary config files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Example model config
        model_config = {
            'models': [
                {
                    'provider': 'OpenAI',
                    'id': 'gpt-4o',
                    'enabled': True,
                    'api_key_env': 'OPENAI_API_KEY'
                }
            ]
        }
        
        # Valid input config
        input_config = {
            'input': [
                {
                    'path': 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/',
                    'images_to_process': 3
                }
            ]
        }
        
        # Create yaml subdirectory and write configs
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'model_config.yaml', 'w') as f:
            yaml.dump(model_config, f)
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        # Test loading
        loader = ConfigLoader(temp_path)
        app_config = loader.load_app_config(verbose=False)
        
        # Assert valid configuration loaded successfully
        assert app_config is not None
        assert len(app_config.enabled_models) == 1
        assert app_config.enabled_models[0].provider == 'OpenAI'


def test_invalid_provider():
    """Test with an invalid provider."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Invalid provider
        model_config = {
            'models': [
                {
                    'provider': 'invalid_provider',  # This should fail
                    'id': 'some-model',
                    'enabled': True,
                    'api_key_env': 'SOME_API_KEY'
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'model_config.yaml', 'w') as f:
            yaml.dump(model_config, f)
        
        loader = ConfigLoader(temp_path)
        with pytest.raises(Exception):  # Should raise ValidationError
            loader.load_models_config()


def test_missing_path():
    """Test with a non-existent path."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Non-existent path
        input_config = {
            'input': [
                {
                    'path': '/this/path/does/not/exist',  # This should fail
                    'images_to_process': 3
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        loader = ConfigLoader(temp_path)
        with pytest.raises(Exception):  # Should raise ValidationError
            loader.load_input_config()


def test_negative_images():
    """Test with negative images_to_process."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Negative images count
        input_config = {
            'input': [
                {
                    'path': 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/',
                    'images_to_process': -1  # This should fail
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        loader = ConfigLoader(temp_path)
        with pytest.raises(Exception):  # Should raise ValidationError
            loader.load_input_config()
