async def get_gguf_variants(
    repo_id: str = Query(
        ..., description = "HuggingFace repo ID (e.g. 'unsloth/gemma-3-4b-it-GGUF')"
    ),
    hf_token: Optional[str] = Query(
        None, description = "HuggingFace token for private repos"
    ),
    current_subject: str = Depends(get_current_subject),
):
    """
    List available GGUF quantization variants for a HuggingFace repo
    or a local directory (e.g. LM Studio model folder).

    Returns all available quantization variants (Q4_K_M, Q8_0, BF16, etc.)
    with file sizes, whether the model supports vision, and the recommended
    default variant.
    """
    try:
        from utils.models.model_config import is_local_path, list_local_gguf_variants

        # Local directory path (e.g. LM Studio models) — scan filesystem
        if is_local_path(repo_id):
            variants, has_vision = list_local_gguf_variants(repo_id)

            filenames = [v.filename for v in variants]
            best = _pick_best_gguf(filenames)
            default_variant = _extract_quant_label(best) if best else None

            return GgufVariantsResponse(
                repo_id = repo_id,
                variants = [
                    GgufVariantDetail(
                        filename = v.filename,
                        quant = v.quant,
                        size_bytes = v.size_bytes,
                        downloaded = True,  # all local variants are downloaded
                    )
                    for v in variants
                ],
                has_vision = has_vision,
                default_variant = default_variant,
            )

        # Remote HuggingFace repo — query HF API
        variants, has_vision = list_gguf_variants(repo_id, hf_token = hf_token)

        # Determine default variant
        filenames = [v.filename for v in variants]
        best = _pick_best_gguf(filenames)
        default_variant = _extract_quant_label(best) if best else None

        # Check which variants are fully downloaded in the HF cache.
        # For split GGUFs, ALL shards must be present -- sum cached bytes
        # per variant and compare against the expected total.
        # HF cache dir uses the exact case from the repo_id at download time,
        # which may differ from the canonical HF repo_id, so do a
        # case-insensitive match.
        cached_bytes_by_quant: dict[str, int] = {}
        try:
            import re as _re
            from huggingface_hub import constants as hf_constants

            # Sanitize repo_id: must be "owner/name" with safe chars only
            if not _is_valid_repo_id(repo_id):
                raise ValueError(f"Invalid repo_id format: {repo_id}")

            cache_dir = Path(hf_constants.HF_HUB_CACHE)
            target = f"models--{repo_id.replace('/', '--')}".lower()
            for entry in cache_dir.iterdir():
                if entry.name.lower() == target:
                    snapshots = entry / "snapshots"
                    if snapshots.is_dir():
                        for snap in snapshots.iterdir():
                            for f in _iter_gguf_paths(snap):
                                q = _extract_quant_label(f.name)
                                cached_bytes_by_quant[q] = (
                                    cached_bytes_by_quant.get(q, 0) + f.stat().st_size
                                )
                    break
        except Exception:
            pass

        def _is_fully_downloaded(variant) -> bool:
            cached = cached_bytes_by_quant.get(variant.quant, 0)
            if cached == 0 or variant.size_bytes == 0:
                return False
            # Allow small rounding tolerance (symlinks vs real sizes)
            return cached >= variant.size_bytes * 0.99

        return GgufVariantsResponse(
            repo_id = repo_id,
            variants = [
                GgufVariantDetail(
                    filename = v.filename,
                    quant = v.quant,
                    size_bytes = v.size_bytes,
                    downloaded = _is_fully_downloaded(v),
                )
                for v in variants
            ],
            has_vision = has_vision,
            default_variant = default_variant,
        )

    except Exception as e:
        logger.error(f"Error listing GGUF variants for '{repo_id}': {e}", exc_info = True)
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to list GGUF variants: {str(e)}",
        )