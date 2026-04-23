def _build_gpu_metrics(
    vram_used_mb,
    vram_total_mb,
    power_draw,
    power_limit,
    **extra,
) -> dict[str, Any]:
    return {
        **extra,
        "vram_used_gb": round(vram_used_mb / 1024, 2)
        if vram_used_mb is not None
        else None,
        "vram_total_gb": round(vram_total_mb / 1024, 2)
        if vram_total_mb is not None
        else None,
        "vram_utilization_pct": round((vram_used_mb / vram_total_mb) * 100, 1)
        if vram_used_mb is not None and vram_total_mb and vram_total_mb > 0
        else None,
        "power_draw_w": power_draw,
        "power_limit_w": power_limit,
        "power_utilization_pct": round((power_draw / power_limit) * 100, 1)
        if power_draw is not None and power_limit and power_limit > 0
        else None,
    }