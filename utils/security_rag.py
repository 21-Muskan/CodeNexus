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
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def chunk_kb(text: str) -> List[Dict[str, str]]:
    """Split the security KB into sections based on '## CWE' headers."""
    sections = []
    current_title = ""
    current_content = []
    
    for line in text.splitlines():
        if line.startswith("## CWE"):
            if current_title:
                sections.append({
                    "title": current_title.strip(),
                    "content": "\\n".join(current_content).strip()
                })
            current_title = line.replace("##", "").strip()
            current_content = []
        else:
            if current_title:
                current_content.append(line)
                
    if current_title:
        sections.append({
            "title": current_title.strip(),
            "content": "\\n".join(current_content).strip()
        })
        
    return sections

def build_security_index(kb_path: str = "data/security_kb.txt", output_file: str = "data/security_index.pkl") -> int:
    """Read the security KB, chunk it, embed, and save to disk."""
    if not os.path.exists(kb_path):
        print(f"Index Builder: KB file {kb_path} not found.")
        return 0
        
    with open(kb_path, "r", encoding="utf-8") as f:
        kb_text = f.read()
        
    chunks = chunk_kb(kb_text)
    
    if not chunks:
        print("No sections found in security KB.")
        return 0
        
    print(f"Index Builder: Extracted {len(chunks)} security patterns. Generating embeddings...")
    model = get_model()
    
    # We embed a combination of the title and content for better retrieval
    texts_to_embed = [chunk["title"] + "\\n" + chunk["content"] for chunk in chunks]
    
    embeddings = model.encode(texts_to_embed, batch_size=8, show_progress_bar=False)
    embeddings_np = np.array(embeddings)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    index_data = {
        "chunks": chunks,
        "embeddings": embeddings_np
    }
    
    with open(output_file, "wb") as f:
        pickle.dump(index_data, f)
        
    print(f"Index Builder: Successfully saved security index to {output_file}")
    return len(chunks)

def get_security_context(code_snippet: str, index_file: str = "data/security_index.pkl", top_k: int = 2) -> str:
    """Embed the code snippet and return the most relevant security patterns as a single formatted string."""
    if not os.path.exists(index_file):
        # Fallback to building it on the fly if it doesn't exist
        print("Security index not found, building it now...")
        build_security_index()
        if not os.path.exists(index_file):
            return "No security context available."
            
    with open(index_file, "rb") as f:
        index_data = pickle.load(f)
        
    chunks = index_data["chunks"]
    embeddings = index_data["embeddings"]
    
    model = get_model()
    # Embed the code snippet to find relevant vulnerabilities
    query_embedding = model.encode([code_snippet])
    
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    context_parts = []
    for idx in top_indices:
        chunk = chunks[idx]
        context_parts.append(f"### {chunk['title']}\\n{chunk['content']}")
        
    return "\\n\\n".join(context_parts)
