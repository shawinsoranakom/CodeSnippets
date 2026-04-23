def search_articles(
    query_text,
    tracking_db_path=None,
    openai_api_key=None,
    index_path="databases/faiss/article_index.faiss",
    mapping_path="databases/faiss/article_id_map.npy",
    top_k=5,
    search_params=None,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    if openai_api_key is None:
        openai_api_key = load_api_key()
        if not openai_api_key:
            raise ValueError("OpenAI API key is required")
    client = OpenAI(api_key=openai_api_key)
    query_embedding, _ = generate_query_embedding(client, query_text)
    if not query_embedding:
        raise ValueError("Failed to generate query embedding")
    query_vector = np.array([query_embedding]).astype(np.float32)
    try:
        faiss_index = load_faiss_index(index_path)
        id_map = load_id_mapping(mapping_path)
        if search_params:
            if isinstance(faiss_index, faiss.IndexIVF) and "nprobe" in search_params:
                faiss_index.nprobe = search_params["nprobe"]
                print(f"Set nprobe to {faiss_index.nprobe}")
            if hasattr(faiss_index, "hnsw") and "ef" in search_params:
                faiss_index.hnsw.efSearch = search_params["ef"]
                print(f"Set efSearch to {faiss_index.hnsw.efSearch}")
        index_type = "unknown"
        if isinstance(faiss_index, faiss.IndexFlatL2):
            index_type = "flat"
        elif isinstance(faiss_index, faiss.IndexIVFFlat):
            index_type = "ivfflat"
            print(f"Using IVF index with nprobe = {faiss_index.nprobe}")
        elif isinstance(faiss_index, faiss.IndexIVFPQ):
            index_type = "ivfpq"
            print(f"Using IVF-PQ index with nprobe = {faiss_index.nprobe}")
        elif hasattr(faiss_index, "hnsw"):
            index_type = "hnsw"
            print(f"Using HNSW index with efSearch = {faiss_index.hnsw.efSearch}")
        print(f"Searching {index_type} FAISS index with {len(id_map)} articles...")
        distances, indices = faiss_index.search(query_vector, top_k)
        result_article_ids = [id_map[idx] for idx in indices[0] if idx < len(id_map)]
        results = get_article_details(tracking_db_path, result_article_ids)
        for i, result in enumerate(results):
            distance = float(distances[0][i])
            similarity = float(np.exp(-distance))
            result["distance"] = distance
            result["similarity"] = similarity
            result["score"] = similarity
        return results
    except Exception as e:
        print(f"Error during search: {str(e)}")
        import traceback

        traceback.print_exc()
        return []