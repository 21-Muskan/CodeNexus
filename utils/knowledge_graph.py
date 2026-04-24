import os
import pickle
import networkx as nx
from typing import List, Dict, Any

try:
    from pyvis.network import Network
except ImportError:
    Network = None

def build_knowledge_graph(chunks: List[Dict[str, Any]]) -> nx.Graph:
    """
    Builds a NetworkX graph linking files/chunks to the concepts extracted from them.
    Assumes each chunk in the list has a 'concepts' list.
    """
    G = nx.Graph()
            
    for chunk in chunks:
        # Fallback if no file path
        file_path = chunk.get('file_path', 'unknown_file')
        start_line = chunk.get('start_line', 1)
        chunk_id = f"{file_path}:L{start_line}"
        
        # Add a node for the code snippet
        G.add_node(chunk_id, type="snippet", label=os.path.basename(file_path))
        
        concepts = chunk.get("concepts", [])
        for concept in concepts:
            # Clean concept string
            concept_clean = str(concept).strip().title()
            if not concept_clean:
                continue
                
            # Add a node for the concept
            G.add_node(concept_clean, type="concept", label=concept_clean)
            
            # Link snippet to concept
            G.add_edge(chunk_id, concept_clean)
            
    return G

def render_graph_html(G: nx.Graph, output_file: str = "data/knowledge_graph.html") -> str:
    """
    Converts a NetworkX graph to an interactive PyVis HTML file.
    Returns the HTML content as a string.
    """
    if Network is None:
        return "<h3>Error: pyvis is not installed</h3>"
        
    if len(G.nodes) == 0:
        return "<h3>No data found to build Knowledge Graph. Please analyze code or build semantic index first.</h3>"
        
    # Create the PyVis network
    net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="white", notebook=False)
    
    # Force layout settings for a good looking graph
    net.force_atlas_2based(central_gravity=0.015, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)
    
    for node_id, attrs in G.nodes(data=True):
        node_type = attrs.get("type", "unknown")
        label = attrs.get("label", str(node_id))
        
        if node_type == "snippet":
            color = "#1f77b4" # Blue
            size = 15
            shape = "dot"
        elif node_type == "concept":
            color = "#ff7f0e" # Orange
            size = 25
            shape = "star"
        else:
            color = "#888888"
            size = 10
            shape = "dot"
            
        net.add_node(node_id, label=label, title=str(node_id), color=color, size=size, shape=shape)
        
    for source, target in G.edges():
        net.add_edge(source, target, color="#555555")
        
    # Generate the HTML
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    net.write_html(output_file)
    
    with open(output_file, "r", encoding="utf-8") as f:
        html_data = f.read()
        
    return html_data
