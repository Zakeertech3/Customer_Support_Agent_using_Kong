import chromadb

def get_chromadb_client():
    try:
        chroma_client = chromadb.HttpClient(host="localhost", port=8002)
        chroma_client.heartbeat()
        return chroma_client
    except Exception as e:
        raise ConnectionError(f"Failed to connect to ChromaDB: {e}")

def get_or_create_collection(client, name="semantic_cache"):
    try:
        return client.get_collection(name=name)
    except ValueError:
        return client.create_collection(name=name)
