def precache_helper_gguf():
    """
    Pre-download the helper GGUF to HF cache.

    Called on FastAPI startup in a background thread so subsequent
    ``_run_with_helper()`` calls skip the download and only pay for
    llama-server startup.  No-op if already cached or disabled.
    """
    if os.environ.get("UNSLOTH_HELPER_MODEL_DISABLE", "").strip() in ("1", "true"):
        return

    repo = os.environ.get("UNSLOTH_HELPER_MODEL_REPO", DEFAULT_HELPER_MODEL_REPO)
    variant = os.environ.get(
        "UNSLOTH_HELPER_MODEL_VARIANT", DEFAULT_HELPER_MODEL_VARIANT
    )

    try:
        from huggingface_hub import HfApi, hf_hub_download
        from huggingface_hub.utils import disable_progress_bars, enable_progress_bars

        disable_progress_bars()
        logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

        # Find the GGUF file matching the variant
        api = HfApi()
        files = api.list_repo_files(repo, repo_type = "model")
        gguf_files = [f for f in files if f.endswith(".gguf")]

        # Find all GGUF files matching the variant (may be split into shards)
        variant_lower = variant.lower().replace("-", "_")
        matching = sorted(
            f for f in gguf_files if variant_lower in f.lower().replace("-", "_")
        )

        if matching:
            logger.info(
                f"Pre-caching helper GGUF: {repo}/{matching[0]}"
                + (f" (+{len(matching) - 1} shards)" if len(matching) > 1 else "")
            )
            for target in matching:
                hf_hub_download(repo_id = repo, filename = target)
            logger.info(f"Helper GGUF cached: {len(matching)} file(s)")
        else:
            logger.warning(f"No GGUF matching variant '{variant}' in {repo}")
    except Exception as e:
        logger.warning(f"Failed to pre-cache helper GGUF: {e}")
    finally:
        try:
            enable_progress_bars()
        except Exception as e:
            pass