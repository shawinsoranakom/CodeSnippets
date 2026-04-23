def configure_amdgpu_asic_id_table_path():
    # Honor an existing valid user-provided path.
    configured = os.environ.get(_AMDGPU_ASIC_ID_TABLE_PATH_ENV, "").strip()
    if configured:
        configured_path = Path(configured)
        try:
            if configured_path.is_file():
                return str(configured_path)
        except Exception:
            pass

    # Only attempt this on ROCm-like environments.
    if not _is_rocm_torch_build():
        return None

    for candidate in _iter_amdgpu_asic_id_table_candidates():
        try:
            if candidate.is_file():
                os.environ[_AMDGPU_ASIC_ID_TABLE_PATH_ENV] = str(candidate)
                if UNSLOTH_ENABLE_LOGGING:
                    logger.info(
                        f"Unsloth: Set {_AMDGPU_ASIC_ID_TABLE_PATH_ENV}={candidate}"
                    )
                return str(candidate)
        except Exception:
            continue

    return None