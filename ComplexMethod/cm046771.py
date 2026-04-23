def get_primary_gpu_utilization() -> dict[str, Any]:
    """Return utilization metrics for the primary visible AMD GPU."""
    gpu_idx = _first_visible_amd_gpu_id()
    if gpu_idx is None:
        return {"available": False}
    data = _run_amd_smi("metric", "-g", gpu_idx)
    if data is None:
        return {"available": False}

    # amd-smi may return:
    #   - a list of GPU dicts (older versions)
    #   - a dict with a "gpu_data" key wrapping a list (newer versions)
    #   - a single GPU dict (rare)
    if isinstance(data, dict) and "gpu_data" in data:
        data = data["gpu_data"]
    if isinstance(data, list):
        if len(data) == 0:
            return {"available": False}
        gpu_data = data[0]
    else:
        gpu_data = data

    metrics = _extract_gpu_metrics(gpu_data)
    if not _has_real_metrics(metrics):
        # amd-smi returned a JSON envelope with no usable fields (error
        # response or unsupported card). Surface as unavailable rather
        # than available-with-empty-data so the UI does not render a
        # ghost device.
        return {"available": False}
    metrics["available"] = True
    return metrics