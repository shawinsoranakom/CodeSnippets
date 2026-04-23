def _has_tokenizer_model(tokenizer, token = None):
    tokenizer = tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
    if tokenizer is None:
        return False

    source = getattr(tokenizer, "name_or_path", None)
    if not isinstance(source, str) or not source:
        return False
    if os.path.isdir(source):
        return os.path.isfile(os.path.join(source, "tokenizer.model"))
    if source in _TOKENIZER_MODEL_CACHE:
        return _TOKENIZER_MODEL_CACHE[source]

    try:
        repo_info = HfApi(token = token).model_info(source, files_metadata = False)
    except Exception:
        return False

    has_tokenizer_model = any(
        sibling.rfilename == "tokenizer.model" for sibling in (repo_info.siblings or [])
    )
    _TOKENIZER_MODEL_CACHE[source] = has_tokenizer_model
    return has_tokenizer_model