def add_embeddings_to_index(embeddings_data, faiss_index, id_map):
    if not embeddings_data:
        return 0, []
    embeddings = []
    article_ids = []
    embedding_ids = []
    for data in embeddings_data:
        try:
            embedding_blob = data["embedding"]
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)

            if embedding.shape[0] != faiss_index.d:
                print(f"Embedding dimension mismatch: expected {faiss_index.d}, got {embedding.shape[0]}")
                continue
            embeddings.append(embedding)
            article_ids.append(data["article_id"])
            embedding_ids.append(data["id"])
        except Exception as e:
            print(f"Error processing embedding {data['id']}: {str(e)}")
    if not embeddings:
        return 0, []
    try:
        embeddings_array = np.vstack(embeddings).astype(np.float32)
        faiss_index.add(embeddings_array)
        for article_id in article_ids:
            id_map.append(article_id)
        print(f"Added {len(embeddings)} embeddings to FAISS index")
        return len(embeddings), embedding_ids
    except Exception as e:
        print(f"Error adding embeddings to FAISS index: {str(e)}")
        return 0, []