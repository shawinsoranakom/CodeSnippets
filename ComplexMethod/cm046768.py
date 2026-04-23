def _parse_memory_mb(value: Any) -> Optional[float]:
    """Parse a memory value from amd-smi output and return MB.

    Handles bare numbers (assumed MB -- the amd-smi convention on every
    version we have seen), dict-shaped values with explicit units
    (``{"value": 192, "unit": "GiB"}`` on newer releases), and plain
    strings like ``"8192 MiB"``.
    """
    unit = ""
    raw_value = value

    if isinstance(value, dict):
        unit = str(value.get("unit", "")).strip().lower()
        raw_value = value.get("value")
    elif isinstance(value, str):
        # Extract unit suffix from strings like "192 GiB" or "8192 MB"
        m = re.match(r"^\s*([\d.]+)\s*([A-Za-z]+)\s*$", value.strip())
        if m:
            unit = m.group(2).lower()

    num = _parse_numeric(raw_value if isinstance(value, dict) else value)
    if num is None:
        return None

    # Unit conversion -- GPU tools (including amd-smi) use binary units even
    # when labeling them "GB" or "MB", so treat GB/GiB and MB/MiB the same.
    if "gib" in unit or "gb" in unit:
        return num * 1024
    if "mib" in unit or "mb" in unit:
        return num
    if "kib" in unit or "kb" in unit:
        return num / 1024
    if unit in ("b", "byte", "bytes"):
        # Plain bytes
        return num / (1024 * 1024)

    # No explicit unit -- default to MB, which is the amd-smi convention
    # for bare numeric values. A previous heuristic assumed values above
    # ~10M were bytes, but that misclassifies small VRAM allocations
    # (e.g. 5 MB = 5,242,880 reported without a unit) as ~5 TB. Modern
    # amd-smi always ships explicit units, so the heuristic branch only
    # fired for legacy output where MB was already the convention.
    return num