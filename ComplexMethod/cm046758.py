def is_embedding_model(model_name: str, hf_token: Optional[str] = None) -> bool:
    """
    Detect embedding/sentence-transformer models using HuggingFace model metadata.

    Uses a belt-and-suspenders approach combining three signals:
      1. "sentence-transformers" in model tags
      2. "feature-extraction" in model tags
      3. pipeline_tag is "sentence-similarity" or "feature-extraction"

    This catches all known embedding models including those like gte-modernbert
    whose library_name is "transformers" rather than "sentence-transformers".

    Args:
        model_name: Model identifier (HF repo or local path)
        hf_token: Optional HF token for accessing gated/private models

    Returns:
        True if the model is an embedding model, False otherwise.
        Defaults to False for local paths or on errors.
    """
    cache_key = (model_name, hf_token)
    if cache_key in _embedding_detection_cache:
        return _embedding_detection_cache[cache_key]

    # Local paths: check for sentence-transformer marker file (modules.json)
    if is_local_path(model_name):
        local_dir = normalize_path(model_name)
        is_emb = os.path.isfile(os.path.join(local_dir, "modules.json"))
        _embedding_detection_cache[cache_key] = is_emb
        return is_emb

    try:
        from huggingface_hub import model_info as hf_model_info

        info = hf_model_info(model_name, token = hf_token)
        tags = set(info.tags or [])
        pipeline_tag = info.pipeline_tag or ""

        is_emb = (
            "sentence-transformers" in tags
            or "feature-extraction" in tags
            or pipeline_tag in ("sentence-similarity", "feature-extraction")
        )

        _embedding_detection_cache[cache_key] = is_emb
        if is_emb:
            logger.info(
                f"Model {model_name} detected as embedding model: "
                f"pipeline_tag={pipeline_tag}, "
                f"sentence-transformers in tags={('sentence-transformers' in tags)}, "
                f"feature-extraction in tags={('feature-extraction' in tags)}"
            )
        return is_emb

    except Exception as e:
        logger.warning(f"Could not determine if {model_name} is embedding model: {e}")
        _embedding_detection_cache[cache_key] = False
        return False