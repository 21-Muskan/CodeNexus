import os
import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Global model instance (lazy loaded)
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Using the same lightweight model as Feature 4 to save memory/time
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def chunk_code(code: str, file_path: str, chunk_size: int = 40) -> List[Dict[str, Any]]:
    """Split code into overlapping chunks of lines."""
    lines = code.splitlines()
    chunks = []
    
    # Simple chunking by lines with slight overlap
    overlap = 5
    for i in range(0, len(lines), chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        if not chunk_lines:
            break
            
        chunk_text = "\\n".join(chunk_lines)
        if chunk_text.strip():
            chunks.append({
                "file_path": file_path,
                "start_line": i + 1,
                "code": chunk_text
            })
            
    return chunks

def build_codebase_index(directory_path: str, output_file: str = "data/semantic_index.pkl") -> int:
    """Walk through python/c++/js/java files, chunk them, embed, and save to disk."""
    supported_exts = {".py", ".cpp", ".c", ".h", ".hpp", ".js", ".jsx", ".ts", ".tsx", ".java"}
    ignore_dirs = {".git", "venv", "node_modules", "__pycache__", "build", "dist", ".pytest_cache"}
    
    all_chunks = []
    print(f"Index Builder: Scanning directory {directory_path}...")
    
    for root, dirs, files in os.walk(directory_path):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                        chunks = chunk_code(code, file_path)
                        all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
                    
    if not all_chunks:
        print("No supported code files found.")
        return 0
        
    print(f"Index Builder: Extracted {len(all_chunks)} chunks. Generating embeddings...")
    model = get_model()
    
    # We embed the code itself (though in a real production MVP we might want to also add docstring metadata)
    texts_to_embed = [chunk["code"] for chunk in all_chunks]
    
    # Encode in batches
    embeddings = model.encode(texts_to_embed, batch_size=32, show_progress_bar=True)
    embeddings_np = np.array(embeddings)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    index_data = {
        "chunks": all_chunks,
        "embeddings": embeddings_np
    }
    
    with open(output_file, "wb") as f:
        pickle.dump(index_data, f)
        
    print(f"Index Builder: Successfully saved vector index to {output_file}")
    return len(all_chunks)

def semantic_search(query: str, index_file: str = "data/semantic_index.pkl", top_k: int = 5) -> List[Dict[str, Any]]:
    """Load index, embed query, and return top_k semantic matches."""
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"Index file {index_file} not found. Please build the index first.")
        
    with open(index_file, "rb") as f:
        index_data = pickle.load(f)
        
    chunks = index_data["chunks"]
    embeddings = index_data["embeddings"]
    
    model = get_model()
    query_embedding = model.encode([query])
    
    # Cosine similarity between query (1x384) and all chunks (Nx384)
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Get top_k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        chunk = chunks[idx]
        score = similarities[idx]
        results.append({
            "file_path": chunk["file_path"],
            "start_line": chunk["start_line"],
            "code": chunk["code"],
            "similarity": float(score)
        })
        
    return results
