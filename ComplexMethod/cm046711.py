def ensure_transformers_version(model_name: str) -> None:
    """Ensure the correct ``transformers`` version is active for *model_name*.

    Uses sys.path with .venv_t5_530/ or .venv_t5_550/ (pre-installed by setup.sh):
      • Need 5.5.0 → prepend .venv_t5_550/ to sys.path, purge modules.
      • Need 5.3.0 → prepend .venv_t5_530/ to sys.path, purge modules.
      • Need 4.x  → remove all .venv_t5_*/ from sys.path, purge modules.

    For LoRA adapters with custom names, the base model is resolved from
    ``adapter_config.json`` before checking.

    NOTE: Training and inference use subprocess isolation instead of this
    function. This is only used by the export path (routes/export.py).
    """
    # Resolve LoRA adapters to their base model for accurate detection
    resolved = _resolve_base_model(model_name)
    tier = get_transformers_tier(resolved)

    if tier == "550":
        target_version = TRANSFORMERS_550_VERSION
        venv_dir = _VENV_T5_550_DIR
        ensure_fn = _ensure_venv_t5_550_exists
    elif tier == "530":
        target_version = TRANSFORMERS_530_VERSION
        venv_dir = _VENV_T5_530_DIR
        ensure_fn = _ensure_venv_t5_530_exists
    else:
        target_version = TRANSFORMERS_DEFAULT_VERSION
        venv_dir = None
        ensure_fn = None

    target_major = int(target_version.split(".")[0])

    # Check what's actually loaded in memory
    in_memory = _get_in_memory_version()

    logger.info(
        "Version check for '%s' (resolved: '%s'): need=%s, in_memory=%s",
        model_name,
        resolved,
        target_version,
        in_memory,
    )

    # --- Already correct? ---------------------------------------------------
    if in_memory is not None:
        if in_memory == target_version:
            logger.info(
                "transformers %s already loaded — correct for '%s'",
                in_memory,
                model_name,
            )
            return
        # Different 5.x → need to switch (e.g. 5.3.0 loaded but need 5.5.0)
        in_memory_major = int(in_memory.split(".")[0])
        if in_memory_major == target_major and venv_dir is None:
            # Both are default (4.x) — close enough
            logger.info(
                "transformers %s already loaded — correct for '%s'",
                in_memory,
                model_name,
            )
            return

    # --- Switch version -----------------------------------------------------
    if venv_dir is not None:
        # First remove any other 5.x venv from sys.path
        _deactivate_5x()
        if not ensure_fn():
            raise RuntimeError(
                f"Cannot activate transformers {target_version}: "
                f"venv missing at {venv_dir}"
            )
        logger.info("Activating transformers %s…", target_version)
        _activate_venv(venv_dir, f"transformers {target_version}")
    else:
        logger.info(
            "Reverting to default transformers %s…", TRANSFORMERS_DEFAULT_VERSION
        )
        _deactivate_5x()

    final = _get_in_memory_version()
    logger.info("✓ transformers version is now %s", final)