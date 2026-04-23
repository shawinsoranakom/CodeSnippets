def _detect_audio_from_tokenizer(
    model_name: str, hf_token: Optional[str] = None
) -> Optional[str]:
    """Detect audio type from tokenizer special tokens (for LLM-based audio models).

    First checks local HF cache, then fetches tokenizer_config.json from HuggingFace.
    Checks added_tokens_decoder for distinctive patterns.
    """

    def _check_token_patterns(tok_config: dict) -> Optional[str]:
        added = tok_config.get("added_tokens_decoder", {})
        if not added:
            return None
        token_contents = [v.get("content", "") for v in added.values()]
        for audio_type, check_fn in _AUDIO_TOKEN_PATTERNS.items():
            if check_fn(token_contents):
                return audio_type
        return None

    # 1) Check local HF cache first (works for gated/offline models)
    try:
        repo_dir = get_cache_path(model_name)
        if repo_dir is not None and repo_dir.exists():
            snapshots_dir = repo_dir / "snapshots"
            if snapshots_dir.exists():
                for snapshot in snapshots_dir.iterdir():
                    for tok_path in [
                        "tokenizer_config.json",
                        "LLM/tokenizer_config.json",
                    ]:
                        tok_file = snapshot / tok_path
                        if tok_file.exists():
                            tok_config = json.loads(tok_file.read_text())
                            result = _check_token_patterns(tok_config)
                            if result:
                                return result
    except Exception as e:
        logger.debug(f"Could not check local cache for {model_name}: {e}")

    # 2) Fall back to HuggingFace API
    try:
        import requests
        import os

        paths_to_try = ["tokenizer_config.json", "LLM/tokenizer_config.json"]
        # Use provided token, or fall back to env
        token = hf_token or os.environ.get("HF_TOKEN")
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        for tok_path in paths_to_try:
            url = f"https://huggingface.co/{model_name}/resolve/main/{tok_path}"
            resp = requests.get(url, headers = headers, timeout = 15)
            if not resp.ok:
                continue

            tok_config = resp.json()
            result = _check_token_patterns(tok_config)
            if result:
                return result

        return None
    except Exception as e:
        logger.debug(
            f"Could not detect audio type from tokenizer for {model_name}: {e}"
        )
        return None