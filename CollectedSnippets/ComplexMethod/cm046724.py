def _run_with_helper(prompt: str, max_tokens: int = 256) -> Optional[str]:
    """
    Load helper model, run one chat completion, unload.

    Returns the completion text, or None on any failure.
    """
    if os.environ.get("UNSLOTH_HELPER_MODEL_DISABLE", "").strip() in ("1", "true"):
        return None

    repo = os.environ.get("UNSLOTH_HELPER_MODEL_REPO", DEFAULT_HELPER_MODEL_REPO)
    variant = os.environ.get(
        "UNSLOTH_HELPER_MODEL_VARIANT", DEFAULT_HELPER_MODEL_VARIANT
    )

    backend = None
    try:
        from core.inference.llama_cpp import LlamaCppBackend

        backend = LlamaCppBackend()
        logger.info(f"Loading helper model: {repo} ({variant})")

        ok = backend.load_model(
            hf_repo = repo,
            hf_variant = variant,
            model_identifier = f"helper:{repo}:{variant}",
            is_vision = False,
            n_ctx = 2048,
            n_gpu_layers = -1,
        )
        if not ok:
            logger.warning("Helper model failed to start")
            return None

        messages = [{"role": "user", "content": prompt}]
        logger.info(
            "Helper model request: enable_thinking=False (per-request override)"
        )
        cumulative = ""
        for chunk in backend.generate_chat_completion(
            messages = messages,
            temperature = 0.1,
            top_p = 0.9,
            top_k = 20,
            max_tokens = max_tokens,
            repetition_penalty = 1.0,
            enable_thinking = False,  # Always disable thinking for AI Assist
        ):
            if isinstance(chunk, dict):
                continue  # skip metadata events
            cumulative = chunk  # cumulative — last value is full text

        result = cumulative.strip()
        result = _strip_think_tags(result)
        logger.info(f"Helper model response ({len(result)} chars)")
        return result if result else None

    except Exception as e:
        logger.warning(f"Helper model failed: {e}")
        return None

    finally:
        if backend is not None:
            try:
                backend.unload_model()
                logger.info("Helper model unloaded")
            except Exception:
                pass