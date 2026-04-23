def _first_visible_amd_gpu_id() -> Optional[str]:
    """Return the physical AMD GPU id that should be treated as 'primary'.

    Honours HIP_VISIBLE_DEVICES / ROCR_VISIBLE_DEVICES / CUDA_VISIBLE_DEVICES
    in that order (HIP respects all three). Returns ``"0"`` when none are
    set, and ``None`` when the env var explicitly narrows to zero GPUs
    ("" or "-1"), so callers can short-circuit to "available: False".
    """
    for env_name in (
        "HIP_VISIBLE_DEVICES",
        "ROCR_VISIBLE_DEVICES",
        "CUDA_VISIBLE_DEVICES",
    ):
        raw = os.environ.get(env_name)
        if raw is None:
            continue
        raw = raw.strip()
        if raw == "" or raw == "-1":
            return None
        # Filter out empty tokens after splitting. This tolerates minor
        # typos like ``HIP_VISIBLE_DEVICES=",1"`` (leading comma, user
        # clearly meant to narrow to device 1) while still falling
        # through to the next env var when every token is empty
        # (e.g. ``,,,``).
        tokens = [t.strip() for t in raw.split(",") if t.strip()]
        if tokens:
            return tokens[0]
    return "0"