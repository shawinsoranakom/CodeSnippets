def embed_descriptions(companies, model_name:str, opts) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    console = Console()
    console.print(f"Using embedding model: [bold cyan]{model_name}[/]")
    cache_path = BASE_DIR / Path(opts.out_dir) / "embeds_cache.json"
    cache = {}
    if cache_path.exists():
        with open(cache_path) as f:
            cache = json.load(f)
        # flush cache if model differs
        if cache.get("_model") != model_name:
            cache = {}

    model = SentenceTransformer(model_name)
    new_texts, new_indices = [], []
    vectors = np.zeros((len(companies), 384), dtype=np.float32)

    for idx, comp in enumerate(companies):
        text = comp.get("about") or comp.get("descriptor","")
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        cached = cache.get(comp["handle"])
        if cached and cached["hash"] == h:
            vectors[idx] = np.array(cached["vector"], dtype=np.float32)
        else:
            new_texts.append(text)
            new_indices.append((idx, comp["handle"], h))

    if new_texts:
        embeds = model.encode(new_texts, show_progress_bar=False, convert_to_numpy=True)
        for vec, (idx, handle, h) in zip(embeds, new_indices):
            vectors[idx] = vec
            cache[handle] = {"hash": h, "vector": vec.tolist()}
        cache["_model"] = model_name
        with open(cache_path, "w") as f:
            json.dump(cache, f)

    return vectors