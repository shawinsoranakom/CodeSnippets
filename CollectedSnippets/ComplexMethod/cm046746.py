def _is_audio_value(value) -> bool:
    """Check if a single sample value looks like audio data."""
    if value is None:
        return False

    # HF datasets Audio feature: decoded → {"array": np.ndarray, "sampling_rate": int}
    if isinstance(value, dict):
        if "array" in value and "sampling_rate" in value:
            return True
        # Undecoded/streaming → {"bytes": b"...", "path": "some.wav"}
        if "bytes" in value or "path" in value:
            path = value.get("path") or ""
            if isinstance(path, str) and any(
                path.lower().endswith(ext) for ext in _AUDIO_EXTENSIONS
            ):
                return True

    return False