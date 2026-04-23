def initialize_faiss_index(dimension=1536, index_path=None, index_type="hnsw", n_list=100):
    if index_path and os.path.exists(index_path):
        print(f"Loading existing FAISS index from {index_path}")
        try:
            index = faiss.read_index(index_path)
            print(f"Loaded index with {index.ntotal} vectors")
            return index
        except Exception as e:
            print(f"Error loading FAISS index: {str(e)}")
            print("Creating a new index instead")
    print(f"Creating new FAISS index with dimension {dimension}, type: {index_type}")
    if index_type == "flat":
        return faiss.IndexFlatL2(dimension)

    elif index_type == "ivfflat":
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, n_list)
        print("Training IVF index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index
    elif index_type == "ivfpq":
        quantizer = faiss.IndexFlatL2(dimension)
        m = 16
        bits = 8
        index = faiss.IndexIVFPQ(quantizer, dimension, n_list, m, bits)
        print("Training IVF-PQ index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index
    elif index_type == "hnsw":
        m = 32
        ef_construction = 100
        index = faiss.IndexHNSWFlat(dimension, m)
        index.hnsw.efConstruction = ef_construction
        index.hnsw.efSearch = 64
        return index
    else:
        print(f"Unknown index type '{index_type}', falling back to IVF Flat")
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFFlat(quantizer, dimension, n_list)
        print("Training IVF index with random vectors...")
        train_size = max(10000, n_list * 10)
        train_vectors = np.random.random((train_size, dimension)).astype(np.float32)
        index.train(train_vectors)
        index.nprobe = min(10, n_list // 10)
        return index