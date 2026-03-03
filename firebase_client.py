"""
Firebase client for real-time state management and data persistence.
Implements robust error handling and connection resilience.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, initialize_app
    from google.cloud.firestore_v1 import Client as FirestoreClient
    from google.cloud.firestore_v1.base_query import FieldFilter
    FIREBASE_AVAILABLE = True
except ImportError as e:
    logging.error(f"Firebase dependencies not available: {e}")
    FIREBASE_AVAILABLE = False

from config import firebase_config

class FirebaseClient:
    """Firebase Firestore client with automatic reconnection and error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client: Optional[FirestoreClient] = None
        self._initialized = False
        
        if not FIREBASE_AVAILABLE:
            self.logger.error("firebase-admin not installed. Run: pip install firebase-admin")
            return
            
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize Firebase connection with credentials"""
        try:
            if firebase_admin._apps:
                # Already initialized
                self.client = firestore.client()
                self.logger.info("Using existing Firebase app")
            else:
                if firebase_config.credentials_path:
                    cred = credentials.Certificate(firebase_config.credentials_path)
                    app = initialize_app(cred)
                elif firebase_config.project_id:
                    # Use default credentials (e.g., GOOGLE_APPLICATION_CREDENTIALS env var)
                    cred = credentials.ApplicationDefault()
                    app = initialize_app(cred, {
                        'projectId': firebase_config.project_id
                    })
                else:
                    raise ValueError("No Firebase credentials provided")
                
                self.client = firestore.client(app)
                self.logger.info(f"Firebase initialized for project: {firebase_config.project_id}")
            
            self._initialized = True
            
        except Exception as e:
            self.logger.error(f"Firebase initialization failed: {e}")
            self._initialized = False
    
    def is_connected(self) -> bool:
        """Check if Firebase connection is active"""
        if not self._initialized or not self.client:
            return False
        
        try:
            # Simple health check - try to list collections
            collections = list(self.client.collections())
            return len(collections) > 0
        except Exception as e:
            self.logger.warning(f"Firebase health check failed: {e}")
            return False
    
    @contextmanager
    def batch_operation(self, max_batch_size: int = 500) -> Any:
        """Context manager for batch operations with automatic commit"""
        if not self._initialized:
            raise ConnectionError("Firebase not initialized")
        
        batch = self.client.batch()
        operations_count = 0
        
        try:
            yield batch
            if operations_count > 0:
                batch.commit()
                self.logger.debug(f"Committed batch with {operations_count} operations")
        except Exception as e:
            self.logger.error(f"Batch operation failed: {e}")
            raise
    
    def save_market_state(self, symbol: str, state_data: Dict[str, Any]) -> bool:
        """Save current market state to Firestore"""
        try:
            if not self._initialized:
                self.logger.error("Firebase not initialized")
                return False
            
            collection = self.client.collection(firebase_config.collection_names["market_state"])
            doc_ref = collection.document(symbol)
            
            # Add timestamp and metadata
            state_data.update({
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "source": "execution_engine"
            })
            
            doc_ref.set(state_data, merge