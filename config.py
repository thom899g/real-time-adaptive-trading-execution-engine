"""
Configuration management for the trading execution engine.
Centralizes all configurable parameters with environment-aware defaults.
"""
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExchangeConfig:
    """Exchange-specific configuration"""
    name: str = "binance"
    api_key: Optional[str] = os.getenv("EXCHANGE_API_KEY")
    api_secret: Optional[str] = os.getenv("EXCHANGE_API_SECRET")
    testnet: bool = os.getenv("EXCHANGE_TESTNET", "true").lower() == "true"
    timeout: int = 30000
    rate_limit: bool = True

@dataclass
class ModelConfig:
    """Machine learning model configuration"""
    volatility_window: int = 100  # Data points for volatility calculation
    liquidity_threshold: float = 0.01  # Minimum liquidity ratio
    training_interval_hours: int = 24
    feature_columns: tuple = ("bid_ask_spread", "order_book_depth", 
                             "volume_24h", "price_variance", "trade_frequency")
    prediction_confidence_threshold: float = 0.7

@dataclass
class ExecutionConfig:
    """Trade execution parameters"""
    max_slippage_pct: float = 0.5
    min_order_size_usd: float = 10.0
    max_order_size_usd: float = 10000.0
    order_type_whitelist: tuple = ("limit", "market", "twap", "vwap")
    default_timeout_seconds: int = 30
    retry_attempts: int = 3
    circuit_breaker_threshold: int = 5  # Max consecutive failures

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    credentials_path: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    collection_names: Dict[str, str] = None
    
    def __post_init__(self):
        if self.collection_names is None:
            self.collection_names = {
                "market_state": "market_state",
                "execution_logs": "execution_logs",
                "model_predictions": "ml_predictions",
                "system_metrics": "system_metrics"
            }

@dataclass
class SystemConfig:
    """System-wide configuration"""
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    health_check_interval_sec: int = 60
    data_stream_buffer_size: int = 1000
    alert_telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    def validate(self) -> bool:
        """Validate critical configuration"""
        required_vars = ["EXCHANGE_API_KEY", "EXCHANGE_API_SECRET"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True

# Global configuration instance
config = SystemConfig()
exchange_config = ExchangeConfig()
model_config = ModelConfig()
execution_config = ExecutionConfig()
firebase_config = FirebaseConfig()