"""Configuration management for IQOS analysis"""
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
        self._create_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = [
            ('data', 'input_file'),
            ('processing', 'mode'),
            ('llm', 'api_endpoint'),
        ]
        
        for section, field in required_fields:
            if section not in self.config or field not in self.config[section]:
                raise ValueError(f"Missing required config: {section}.{field}")
        
        # Validate processing mode
        mode = self.config['processing']['mode']
        if mode not in ['sample', 'full']:
            raise ValueError(f"Invalid processing mode: {mode}. Must be 'sample' or 'full'")
        
        # Validate input file exists
        input_file = Path(self.config['data']['input_file'])
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
    
    def _create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config['data']['output_dir'],
            self.config['data']['image_cache_dir'],
            self.config['data']['processed_state_dir'],
            'output/logs'
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, *keys, default=None):
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    @property
    def is_sample_mode(self) -> bool:
        """Check if running in sample mode"""
        return self.config['processing']['mode'] == 'sample'
    
    @property
    def sample_size(self) -> int:
        """Get sample size"""
        return self.config['processing'].get('sample_size', 50)
    
    @property
    def input_file(self) -> Path:
        """Get input file path"""
        return Path(self.config['data']['input_file'])
    
    def __repr__(self):
        return f"Config(mode={self.config['processing']['mode']}, input={self.input_file.name})"