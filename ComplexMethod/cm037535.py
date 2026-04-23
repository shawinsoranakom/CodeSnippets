def merge_media_io_kwargs(
    defaults: dict[str, dict[str, Any]] | None,
    overrides: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]] | None:
    """Merge config-level and per-request media_io_kwargs per modality.

    Each modality key is merged using the corresponding MediaIO subclass's
    ``merge_kwargs``, which may apply modality-specific logic (e.g.
    VideoMediaIO clears cross-dependent fps/num_frames fields).
    """
    if not defaults and not overrides:
        return None
    all_keys = set(defaults or {}) | set(overrides or {})
    merged = {}
    for key in all_keys:
        io_cls = MODALITY_IO_MAP.get(key, MediaIO)
        merged[key] = io_cls.merge_kwargs(
            (defaults or {}).get(key),
            (overrides or {}).get(key),
        )
    return merged or None