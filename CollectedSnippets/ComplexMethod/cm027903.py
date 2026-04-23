def process_embeddings_for_indexing(
    tracking_db_path=None,
    index_path=None,
    mapping_path=None,
    batch_size=100,
    index_type="ivfflat",
    n_list=100,
):
    if tracking_db_path is None:
        tracking_db_path = get_tracking_db_path()
    index_dir = os.path.dirname(index_path)
    os.makedirs(index_dir, exist_ok=True)
    id_map = load_id_mapping(mapping_path)
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='article_embeddings'
        """)
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("article_embeddings table does not exist. Please run embedding_processor first.")
            return {"processed": 0, "added": 0, "errors": 0, "total_vectors": 0, "status": "table_missing"}
    sample_query = """
    SELECT embedding FROM article_embeddings LIMIT 1
    """
    sample = execute_query(tracking_db_path, sample_query, fetch=True, fetch_one=True)
    if not sample:
        print("No embeddings found in the database")
        default_dimension = 1536
        print(f"Using default dimension: {default_dimension}")

        faiss_index = initialize_faiss_index(
            dimension=default_dimension, index_path=index_path if os.path.exists(index_path) else None, index_type=index_type, n_list=n_list
        )
        return {
            "processed": 0,
            "added": 0,
            "errors": 0,
            "total_vectors": faiss_index.ntotal if hasattr(faiss_index, "ntotal") else 0,
            "status": "no_embeddings",
        }
    embedding_dimension = len(np.frombuffer(sample["embedding"], dtype=np.float32))
    print(f"Detected embedding dimension: {embedding_dimension}")
    faiss_index = initialize_faiss_index(dimension=embedding_dimension, index_path=index_path, index_type=index_type, n_list=n_list)
    embeddings_data = get_embeddings_not_in_index(tracking_db_path, limit=batch_size)
    if not embeddings_data:
        print("No new embeddings to add to the index")
        return {"processed": 0, "added": 0, "errors": 0, "total_vectors": faiss_index.ntotal, "status": "no_new_embeddings"}
    added_count, embedding_ids = add_embeddings_to_index(embeddings_data, faiss_index, id_map)
    if added_count > 0:
        save_faiss_index(faiss_index, index_path)
        save_id_mapping(id_map, mapping_path)
        marked_count = mark_embeddings_as_indexed(tracking_db_path, embedding_ids)
        print(f"Marked {marked_count} embeddings as indexed in the database")
    stats = {
        "processed": len(embeddings_data),
        "added": added_count,
        "errors": len(embeddings_data) - added_count,
        "total_vectors": faiss_index.ntotal,
        "index_type": index_type,
        "status": "success",
    }
    return stats