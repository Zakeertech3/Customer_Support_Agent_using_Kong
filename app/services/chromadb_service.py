import chromadb
import logging
from typing import List, Dict, Any, Optional
from chromadb.config import Settings
from app.config import config

logger = logging.getLogger(__name__)

class ChromaDBService:
    def __init__(self):
        self.client = None
        self.collections = {}
        self.is_connected = False
        
    def initialize(self) -> bool:
        try:
            self.client = chromadb.HttpClient(
                host=config.chromadb.host,
                port=config.chromadb.port
            )
            
            self._create_collections()
            self.is_connected = True
            logger.info("ChromaDB connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.is_connected = False
            return False
    
    def _create_collections(self):
        collection_names = [
            config.chromadb.simple_collection,
            config.chromadb.complex_collection,
            config.chromadb.fallback_collection
        ]
        
        for collection_name in collection_names:
            try:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections[collection_name] = collection
                logger.info(f"Collection '{collection_name}' initialized")
                
            except Exception as e:
                logger.error(f"Failed to create collection '{collection_name}': {e}")
    
    def add_to_cache(self, collection_name: str, query: str, response: str, metadata: Dict[str, Any] = None) -> bool:
        if not self.is_connected or collection_name not in self.collections:
            return False
            
        try:
            collection = self.collections[collection_name]
            
            doc_id = f"cache_{hash(query)}_{len(collection.get()['ids'])}"
            
            collection.add(
                documents=[query],
                metadatas=[{
                    "response": response,
                    "timestamp": metadata.get("timestamp", ""),
                    "model": metadata.get("model", ""),
                    **(metadata or {})
                }],
                ids=[doc_id]
            )
            
            logger.debug(f"Added cache entry to '{collection_name}': {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add cache entry: {e}")
            return False
    
    def search_cache(self, collection_name: str, query: str, similarity_threshold: float = None) -> Optional[Dict[str, Any]]:
        if not self.is_connected or collection_name not in self.collections:
            return None
            
        try:
            collection = self.collections[collection_name]
            threshold = similarity_threshold or config.cache.similarity_threshold
            
            results = collection.query(
                query_texts=[query],
                n_results=1
            )
            
            if results['documents'] and results['distances']:
                distance = results['distances'][0][0]
                similarity = 1 - distance
                
                if similarity >= threshold:
                    metadata = results['metadatas'][0][0]
                    return {
                        "response": metadata.get("response"),
                        "similarity": similarity,
                        "metadata": metadata
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to search cache: {e}")
            return None
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        if not self.is_connected or collection_name not in self.collections:
            return {"count": 0, "status": "disconnected"}
            
        try:
            collection = self.collections[collection_name]
            data = collection.get()
            
            return {
                "count": len(data['ids']),
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"count": 0, "status": "error"}
    
    def clear_collection(self, collection_name: str) -> bool:
        if not self.is_connected or collection_name not in self.collections:
            return False
            
        try:
            self.client.delete_collection(collection_name)
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.collections[collection_name] = collection
            
            logger.info(f"Collection '{collection_name}' cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection '{collection_name}': {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        try:
            if not self.client:
                return {"status": "disconnected", "message": "Client not initialized"}
                
            heartbeat = self.client.heartbeat()
            
            collections_status = {}
            for name, collection in self.collections.items():
                try:
                    data = collection.get()
                    collections_status[name] = {
                        "status": "healthy",
                        "count": len(data['ids'])
                    }
                except Exception as e:
                    collections_status[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "status": "healthy",
                "heartbeat": heartbeat,
                "collections": collections_status,
                "connection": self.is_connected
            }
            
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": False
            }

chromadb_service = ChromaDBService()
