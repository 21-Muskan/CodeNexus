# from huggingface_hub import snapshot_download
from pathlib import Path

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.retrievers import VectorIndexRetriever

import math
import os
from fastmcp import FastMCP

current_directory = os.getcwd()
print(f"Current working directory: {current_directory}")
if os.path.basename(current_directory) == "server":
    directory_path = os.path.join(".", "embedding_model")
else:
    directory_path = os.path.join(".", "server", "embedding_model")

if Path(directory_path).is_dir():
    print(f"The directory '{directory_path}' exists.")
else:
    print(f"Downloading 'embedding_model'.")
    model_id = "BAAI/bge-base-en-v1.5"
    local_dir = directory_path
    # snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False)


embed_model = HuggingFaceEmbedding(
    model_name=directory_path
)
Settings.embed_model = embed_model

if os.path.basename(current_directory) == "server":
    storage_path = os.path.join(".", "storage")
else:
    storage_path = os.path.join(".", "server", "storage")

storage_context = StorageContext.from_defaults(persist_dir=storage_path)
index = load_index_from_storage(storage_context=storage_context)
retriever = VectorIndexRetriever(index=index, similarity_top_k=20)

# nodes = retriever.retrieve("what is the range of vForceRange parameters")
# for ele in nodes:
#     print(ele,"\n\n")


mcp= FastMCP("ABH_Server",port=8003)

@mcp.tool()
def add(a: int, b: int) -> int:
   print(f"Server received add request: {a}, {b}")
   return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
   print(f"Server received multiply request: {a}, {b}")
   return a * b

@mcp.tool()
def sine(a: int) -> float:
    print(f"Server received sine request: {a}")
    radians = math.radians(a)  # Convert from degrees to radians
    result = math.sin(radians)
    print(f"Sine of {a} degrees (radians: {radians}): {result}")
    return result

@mcp.tool()
def list_files_and_folders() -> list:
    """
    Lists all files and directories in the current working directory.
    Returns:
        A list of strings, each representing a file or folder.
    """
    print("Server received request to list files and folders.")
    try:
        # Get all files and directories in the current working directory
        items = os.listdir(".")
        print(f"Files and Folders in Current Directory: {items}")
        return items
    except Exception as e:
        print(f"Error listing files and folders: {e}")
        return [f"Error: {str(e)}"]
    
@mcp.tool()
def search_documents(query: str) -> list:
    """
    Searches documents using vector similarity retrieval.
    
    Args:
        query (str): The search query string to find relevant documents.
        
    Returns:
        list: A list of dictionaries, each containing:
            - text (str): The retrieved document text content
            - score (float): The similarity score of the document to the query
    """
    print(f"Server received search_documents request: {query}")
    nodes = retriever.retrieve(query)
    return [{"text" : ele.get_text(), "score" : ele.get_score()} for ele in nodes]

if __name__ =="__main__":
   print("Starting MCP Server....")
   mcp.run(transport="sse")
#    mcp.run(transport="stdio")