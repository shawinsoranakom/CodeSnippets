def _extract_gpu_metrics(gpu_data: dict) -> dict[str, Any]:
    """Extract standardized metrics from a single GPU's amd-smi data."""
    # amd-smi metric output structure varies by version; try common paths
    usage = gpu_data.get("usage", gpu_data.get("gpu_activity", {}))
    if isinstance(usage, dict):
        gpu_util = _parse_numeric(
            usage.get("gfx_activity", usage.get("gpu_use_percent"))
        )
    else:
        gpu_util = _parse_numeric(usage)

    # Temperature -- try multiple keys in priority order.
    # dict.get() returns "N/A" strings rather than falling through,
    # so we must try each key and check if it parses to a real number.
    temp_data = gpu_data.get("temperature", {})
    temp = None
    if isinstance(temp_data, dict):
        for temp_key in ("edge", "temperature_edge", "hotspot", "temperature_hotspot"):
            temp = _parse_numeric(temp_data.get(temp_key))
            if temp is not None:
                break
    else:
        temp = _parse_numeric(temp_data)

    # Power
    power_data = gpu_data.get("power", {})
    if isinstance(power_data, dict):
        power_draw = _parse_numeric(
            power_data.get(
                "current_socket_power",
                power_data.get("average_socket_power", power_data.get("socket_power")),
            )
        )
        power_limit = _parse_numeric(
            power_data.get("power_cap", power_data.get("max_power_limit"))
        )
    else:
        power_draw = None
        power_limit = None

    # VRAM -- unit-aware parsing to handle varying amd-smi output formats.
    # Newer amd-smi versions may return {"value": 192, "unit": "GiB"}.
    # Newer amd-smi uses "mem_usage" with "total_vram" / "used_vram" keys;
    # older versions use "vram" or "fb_memory_usage" with "used" / "total".
    vram_data = gpu_data.get(
        "mem_usage",
        gpu_data.get("vram", gpu_data.get("fb_memory_usage", {})),
    )
    if isinstance(vram_data, dict):
        vram_used_mb = _parse_memory_mb(
            vram_data.get(
                "used_vram", vram_data.get("vram_used", vram_data.get("used"))
            )
        )
        vram_total_mb = _parse_memory_mb(
            vram_data.get(
                "total_vram", vram_data.get("vram_total", vram_data.get("total"))
            )
        )
    else:
        vram_used_mb = None
        vram_total_mb = None

    # Build the standardized dict (same shape as nvidia._build_gpu_metrics)
    vram_used_gb = round(vram_used_mb / 1024, 2) if vram_used_mb is not None else None
    vram_total_gb = (
        round(vram_total_mb / 1024, 2) if vram_total_mb is not None else None
    )
    vram_util = (
        round((vram_used_mb / vram_total_mb) * 100, 1)
        if vram_used_mb is not None and vram_total_mb is not None and vram_total_mb > 0
        else None
    )
    power_util = (
        round((power_draw / power_limit) * 100, 1)
        if power_draw is not None and power_limit is not None and power_limit > 0
        else None
    )

    return {
        "gpu_utilization_pct": gpu_util,
        "temperature_c": temp,
        "vram_used_gb": vram_used_gb,
        "vram_total_gb": vram_total_gb,
        "vram_utilization_pct": vram_util,
        "power_draw_w": power_draw,
        "power_limit_w": power_limit,
        "power_utilization_pct": power_util,
    }