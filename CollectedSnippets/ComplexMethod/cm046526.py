async def list_local_models(
    models_dir: str = Query(
        default = "./models", description = "Directory to scan for local model folders"
    ),
    current_subject: str = Depends(get_current_subject),
):
    """
    List local model candidates from custom models dir, HF cache,
    legacy Unsloth HF cache, and LM Studio directories.
    """
    from utils.paths import (
        legacy_hf_cache_dir,
        hf_default_cache_dir,
        lmstudio_model_dirs,
    )

    # Resolve all scan directories up front.
    hf_cache_dir = _resolve_hf_cache_dir()
    legacy_hf = legacy_hf_cache_dir()
    hf_default = hf_default_cache_dir()
    lm_dirs = lmstudio_model_dirs()

    # Validate models_dir against an allowlist of trusted directories.
    # Only the trusted Path objects are used for filesystem access -- the
    # user-supplied string is only used for matching, never for path construction.
    allowed_roots: list[Path] = [Path("./models").resolve(), hf_cache_dir]
    if legacy_hf.is_dir():
        allowed_roots.append(legacy_hf)
    if hf_default.is_dir():
        allowed_roots.append(hf_default)
    try:
        from utils.paths import studio_root, outputs_root

        allowed_roots.extend([studio_root(), outputs_root()])
    except Exception:
        pass

    requested = os.path.realpath(os.path.expanduser(models_dir))
    models_root = None
    for root in allowed_roots:
        root_str = os.path.realpath(str(root))
        if requested == root_str or requested.startswith(root_str + os.sep):
            models_root = root  # Use the trusted root, not the user-supplied path
            break
    if models_root is None:
        raise HTTPException(
            status_code = 403,
            detail = "Directory not allowed",
        )

    try:
        local_models = _scan_models_dir(models_root) + _scan_hf_cache(hf_cache_dir)

        # Scan legacy Unsloth HF cache for backward compatibility
        if legacy_hf.is_dir() and legacy_hf.resolve() != hf_cache_dir.resolve():
            local_models += _scan_hf_cache(legacy_hf)

        # Scan HF system default cache (may differ when env vars are overridden)
        if (
            hf_default.is_dir()
            and hf_default.resolve() != hf_cache_dir.resolve()
            and hf_default.resolve() != legacy_hf.resolve()
        ):
            local_models += _scan_hf_cache(hf_default)

        # Scan LM Studio directories
        for lm_dir in lm_dirs:
            local_models += _scan_lmstudio_dir(lm_dir)

        # Scan user-added custom folders (cap per-folder to avoid unbounded scans)
        from storage.studio_db import list_scan_folders

        _MAX_MODELS_PER_FOLDER = 200
        try:
            custom_folders = list_scan_folders()
        except Exception as e:
            logger.warning("Could not load custom scan folders: %s", e)
            custom_folders = []
        for folder in custom_folders:
            folder_path = Path(folder["path"])
            try:
                # Ollama scanner creates .studio_links/ with .gguf symlinks.
                # Filter those from the generic scanners to avoid duplicates
                # and leaking internal paths into the UI.
                _generic = [
                    m
                    for m in (
                        _scan_models_dir(folder_path, limit = _MAX_MODELS_PER_FOLDER)
                        + _scan_hf_cache(folder_path)
                        + _scan_lmstudio_dir(folder_path)
                    )
                    if not any(
                        p in (".studio_links", "ollama_links")
                        for p in Path(m.path).parts
                    )
                ]
                custom_models = _generic
                if len(custom_models) < _MAX_MODELS_PER_FOLDER:
                    custom_models += _scan_ollama_dir(
                        folder_path,
                        limit = _MAX_MODELS_PER_FOLDER - len(custom_models),
                    )
            except OSError as e:
                logger.warning("Skipping unreadable scan folder %s: %s", folder_path, e)
                continue
            local_models += [
                m.model_copy(update = {"source": "custom"}) for m in custom_models
            ]

        # Deduplicate models, but always keep custom folder entries so they
        # appear in the "Custom Folders" UI section even when the same model
        # also exists in the HF cache or default models directory.  Use a
        # (id, source) key for custom entries to avoid collisions.
        deduped: dict[str, LocalModelInfo] = {}
        for model in local_models:
            key = f"{model.id}\x00custom" if model.source == "custom" else model.id
            if key not in deduped:
                deduped[key] = model

        models = sorted(
            deduped.values(),
            key = lambda item: (item.updated_at or 0),
            reverse = True,
        )

        return LocalModelListResponse(
            models_dir = str(models_root),
            hf_cache_dir = str(hf_cache_dir),
            lmstudio_dirs = [str(d) for d in lm_dirs],
            models = models,
        )
    except Exception as e:
        logger.error(f"Error listing local models: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to list local models: {str(e)}",
        )