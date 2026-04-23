def activate_transformers_for_subprocess(model_name: str) -> None:
    """Activate the correct transformers version in a subprocess worker.

    Call this BEFORE any ML imports. Resolves LoRA adapters to their base
    model, determines the required tier, and prepends the appropriate
    ``.venv_t5_*`` directory to ``sys.path``.  Also propagates the path
    via ``PYTHONPATH`` for child processes (e.g. GGUF converter).

    Used by training, inference, and export workers.
    """
    resolved = _resolve_base_model(model_name)
    tier = get_transformers_tier(resolved)

    if tier == "550":
        if not _ensure_venv_t5_550_exists():
            raise RuntimeError(
                f"Cannot activate transformers 5.5.0: "
                f".venv_t5_550 missing at {_VENV_T5_550_DIR}"
            )
        if _VENV_T5_550_DIR not in sys.path:
            sys.path.insert(0, _VENV_T5_550_DIR)
        logger.info("Activated transformers 5.5.0 from %s", _VENV_T5_550_DIR)
        _pp = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = _VENV_T5_550_DIR + (os.pathsep + _pp if _pp else "")
    elif tier == "530":
        if not _ensure_venv_t5_530_exists():
            raise RuntimeError(
                f"Cannot activate transformers 5.3.0: "
                f".venv_t5_530 missing at {_VENV_T5_530_DIR}"
            )
        if _VENV_T5_530_DIR not in sys.path:
            sys.path.insert(0, _VENV_T5_530_DIR)
        logger.info("Activated transformers 5.3.0 from %s", _VENV_T5_530_DIR)
        _pp = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = _VENV_T5_530_DIR + (os.pathsep + _pp if _pp else "")
    else:
        logger.info("Using default transformers (4.57.x) for %s", model_name)