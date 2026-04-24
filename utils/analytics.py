import pandas as pd
import numpy as np
from typing import Dict, Any

def generate_bug_clusters(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Take a DataFrame with a 'Code', 'Explanation', and 'Error Type' column,
    generate embeddings for the explanations, and cluster them using K-Means.
    
    Returns a dictionary with:
      - 'df': the modified DataFrame with 'Cluster', 'x', and 'y' columns for 2D plotting.
      - 'top_types': a Series of the most common 'Error Type' tags.
      - 'cluster_summary': a dict mapping Cluster ID -> list of top 3 explanations.
    """
    if "Explanation" not in df.columns:
        raise ValueError("DataFrame must contain an 'Explanation' column.")
        
    # Filter out rows where no bugs were detected
    # Assuming "No bugs detected" or similar is the default string
    mask = df["Explanation"].str.contains("No bugs detected", case=False, na=False)
    bug_df = df[~mask].copy()
    
    if len(bug_df) == 0:
        return {
            "df": pd.DataFrame(),
            "top_types": pd.Series(dtype=int),
            "cluster_summary": {}
        }
        
    # 1. Generate Embeddings
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
        
    # all-MiniLM-L6-v2 is small and fast for text clustering
    model = SentenceTransformer('all-MiniLM-L6-v2')
    explanations = bug_df["Explanation"].tolist()
    embeddings = model.encode(explanations)
    
    # 2. Cluster using K-Means
    from sklearn.cluster import KMeans
    # Choose k based on data size (min 2, max 5, or half the data points)
    n_samples = len(bug_df)
    k = min(5, max(2, n_samples // 3))
    
    if n_samples < 3:
        # Too little data to cluster meaningfully, just set all to 0
        bug_df["Cluster"] = 0
        bug_df["x"] = np.zeros(n_samples)
        bug_df["y"] = np.zeros(n_samples)
    else:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        bug_df["Cluster"] = kmeans.fit_predict(embeddings)
        
        # 3. Project to 2D for visualization using PCA
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(embeddings)
        bug_df["x"] = coords[:, 0]
        bug_df["y"] = coords[:, 1]
        
    # Ensure Cluster is string/categorical for discrete colors in Plotly
    bug_df["Cluster"] = bug_df["Cluster"].apply(lambda c: f"Cluster {c}")
        
    # 4. Aggregations
    top_types = pd.Series(dtype=int)
    if "Error Type" in bug_df.columns:
        # Error Type might be semi-colon separated (e.g., "SyntaxError; Logic Error")
        all_types = bug_df["Error Type"].dropna().str.split(";").explode().str.strip()
        top_types = all_types.value_counts()
        
    # Extract 3 example explanations per cluster for summary
    cluster_summary = {}
    for cluster_name in bug_df["Cluster"].unique():
        examples = bug_df[bug_df["Cluster"] == cluster_name]["Explanation"].head(3).tolist()
        cluster_summary[cluster_name] = examples
        
    return {
        "df": bug_df,
        "top_types": top_types,
        "cluster_summary": cluster_summary
    }
