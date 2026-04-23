def _extract_safetensors_metadata(
    header: dict[str, Any], meta: ExtractedMetadata
) -> None:
    """Extract metadata from safetensors header __metadata__ section.

    Modifies meta in-place.
    """
    st_meta = header.get("__metadata__", {})
    if not isinstance(st_meta, dict):
        return

    # Common model metadata
    meta.base_model = (
        st_meta.get("ss_base_model_version")
        or st_meta.get("modelspec.base_model")
        or st_meta.get("base_model")
    )

    # Trained words / trigger words
    trained_words = st_meta.get("ss_tag_frequency")
    if trained_words and isinstance(trained_words, str):
        try:
            tag_freq = json.loads(trained_words)
            # Extract unique tags from all datasets
            all_tags: set[str] = set()
            for dataset_tags in tag_freq.values():
                if isinstance(dataset_tags, dict):
                    all_tags.update(dataset_tags.keys())
            if all_tags:
                meta.trained_words = sorted(all_tags)[:100]
        except json.JSONDecodeError:
            pass

    # Direct trained_words field (some formats)
    if not meta.trained_words:
        tw = st_meta.get("trained_words")
        if isinstance(tw, str):
            try:
                parsed = json.loads(tw)
                if isinstance(parsed, list):
                    meta.trained_words = [str(x) for x in parsed]
                else:
                    meta.trained_words = [w.strip() for w in tw.split(",") if w.strip()]
            except json.JSONDecodeError:
                meta.trained_words = [w.strip() for w in tw.split(",") if w.strip()]
        elif isinstance(tw, list):
            meta.trained_words = [str(x) for x in tw]

    # CivitAI AIR
    meta.air = st_meta.get("air") or st_meta.get("modelspec.air")

    # Preview images (ssmd_cover_images)
    cover_images = st_meta.get("ssmd_cover_images")
    if cover_images:
        meta.has_preview_images = True

    # Source provenance fields
    meta.source_url = st_meta.get("source_url")
    meta.source_arn = st_meta.get("source_arn")
    meta.repo_url = st_meta.get("repo_url")
    meta.preview_url = st_meta.get("preview_url")
    meta.source_hash = st_meta.get("source_hash") or st_meta.get("sshs_model_hash")

    # HuggingFace fields
    meta.repo_id = st_meta.get("repo_id") or st_meta.get("hf_repo_id")
    meta.revision = st_meta.get("revision") or st_meta.get("hf_revision")
    meta.filepath = st_meta.get("filepath") or st_meta.get("hf_filepath")
    meta.resolve_url = st_meta.get("resolve_url") or st_meta.get("hf_url")