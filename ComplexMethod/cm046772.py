def get_visible_gpu_utilization(
    parent_visible_ids: Optional[list[int]],
    parent_cuda_visible_devices: Optional[str] = None,
) -> dict[str, Any]:
    """Return utilization metrics for visible AMD GPUs."""
    if parent_visible_ids is None:
        return {
            "available": False,
            "backend_cuda_visible_devices": parent_cuda_visible_devices,
            "parent_visible_gpu_ids": [],
            "devices": [],
            "index_kind": "unresolved",
        }

    data = _run_amd_smi("metric")
    if data is None:
        return {
            "available": False,
            "backend_cuda_visible_devices": parent_cuda_visible_devices,
            "parent_visible_gpu_ids": parent_visible_ids or [],
            "devices": [],
            "index_kind": "physical",
        }

    # Extract a device list from amd-smi's envelope. Newer versions return
    # a JSON array directly, older versions return a dict with a "gpus" /
    # "gpu" key wrapping the list. Guard non-dict / non-list envelopes
    # (scalar / string fallbacks from malformed output) so the .get()
    # access cannot raise AttributeError on an unexpected shape.
    if isinstance(data, list):
        gpu_list = data
    elif isinstance(data, dict):
        # Newer amd-smi wraps output in {"gpu_data": [...]}
        gpu_list = data.get("gpu_data", data.get("gpus", data.get("gpu", [data])))
    else:
        gpu_list = [data]
    visible_set = set(parent_visible_ids)
    ordinal_map = {gpu_id: ordinal for ordinal, gpu_id in enumerate(parent_visible_ids)}

    devices = []
    for fallback_idx, gpu_data in enumerate(gpu_list):
        # Skip non-dict entries defensively: if amd-smi ever ships a
        # scalar inside its "gpus" array (observed on some malformed
        # output), _extract_gpu_metrics would raise AttributeError on
        # the first .get() call.
        if not isinstance(gpu_data, dict):
            continue
        # Use AMD-reported GPU ID when available, fall back to enumeration
        # index. Newer amd-smi versions wrap scalars as ``{"value": 0,
        # "unit": "none"}``, so route raw_id through ``_parse_numeric``
        # which already handles bare ints, floats, strings, and that
        # dict shape uniformly.
        raw_id = gpu_data.get(
            "gpu", gpu_data.get("gpu_id", gpu_data.get("id", fallback_idx))
        )
        parsed_id = _parse_numeric(raw_id)
        if parsed_id is None:
            logger.debug(
                "amd-smi GPU id %r could not be parsed; falling back to "
                "enumeration index %d",
                raw_id,
                fallback_idx,
            )
            idx = fallback_idx
        else:
            idx = int(parsed_id)
        if idx not in visible_set:
            continue
        metrics = _extract_gpu_metrics(gpu_data)
        if not _has_real_metrics(metrics):
            # Skip ghost entries: an amd-smi response that decodes to a
            # dict but contains no usable fields (error envelope, etc.)
            # would otherwise show up as a device row with all-None
            # numbers in the UI.
            continue
        metrics["index"] = idx
        metrics["index_kind"] = "physical"
        metrics["visible_ordinal"] = ordinal_map.get(idx, len(devices))
        devices.append(metrics)

    return {
        "available": len(devices) > 0,
        "backend_cuda_visible_devices": parent_cuda_visible_devices,
        "parent_visible_gpu_ids": parent_visible_ids or [],
        "devices": devices,
        "index_kind": "physical",
    }