async def get_text_embeddings(
    texts: List[str], 
    llm_config: Optional[Dict] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 32
) -> np.ndarray:
    """
    Compute embeddings for a list of texts using specified model.

    Args:
        texts: List of texts to embed
        llm_config: Optional LLM configuration for API-based embeddings
        model_name: Model name (used when llm_config is None)
        batch_size: Batch size for processing

    Returns:
        numpy array of embeddings
    """
    import numpy as np

    if not texts:
        return np.array([])

    # If LLMConfig provided, use litellm for embeddings
    if llm_config is not None:
        from litellm import aembedding

        # Get embedding model from config or use default
        embedding_model = llm_config.get('provider', 'text-embedding-3-small')
        api_base = llm_config.get('base_url', llm_config.get('api_base'))

        # Prepare kwargs
        kwargs = {
            'model': embedding_model,
            'input': texts,
            'api_key': llm_config.get('api_token', llm_config.get('api_key'))
        }

        if api_base:
            kwargs['api_base'] = api_base

        # Handle OpenAI-compatible endpoints
        if api_base and 'openai/' not in embedding_model:
            kwargs['model'] = f"openai/{embedding_model}"

        # Get embeddings
        response = await aembedding(**kwargs)

        # Extract embeddings from response
        embeddings = []
        for item in response.data:
            embeddings.append(item['embedding'])

        return np.array(embeddings)

    # Default: use sentence-transformers
    else:
        # Lazy load to avoid importing heavy libraries unless needed
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install it with: pip install 'crawl4ai[transformer]' or pip install sentence-transformers"
            )

        # Cache the model in function attribute to avoid reloading
        if not hasattr(get_text_embeddings, '_models'):
            get_text_embeddings._models = {}

        if model_name not in get_text_embeddings._models:
            get_text_embeddings._models[model_name] = SentenceTransformer(model_name)

        encoder = get_text_embeddings._models[model_name]

        # Batch encode for efficiency
        embeddings = encoder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return embeddings