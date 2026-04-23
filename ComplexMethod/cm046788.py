def get_visible_gpu_utilization(
    parent_visible_ids: Optional[list[int]],
    parent_cuda_visible_devices: Optional[str] = None,
) -> dict[str, Any]:
    # When parent_visible_ids is None (UUID/MIG mask), we cannot safely
    # map nvidia-smi rows to the process's visible devices. Return empty
    # instead of exposing all physical GPUs.
    if parent_visible_ids is None:
        return {
            "available": False,
            "backend_cuda_visible_devices": parent_cuda_visible_devices,
            "parent_visible_gpu_ids": [],
            "devices": [],
            "index_kind": "unresolved",
        }
    visible_ordinals = _visible_ordinal_map(parent_visible_ids)
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,utilization.gpu,temperature.gpu,"
                "memory.used,memory.total,power.draw,power.limit",
                "--format=csv,noheader,nounits",
            ],
            capture_output = True,
            text = True,
            timeout = 5,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning("nvidia-smi query failed in get_visible_gpu_utilization: %s", e)
        return {
            "available": False,
            "backend_cuda_visible_devices": parent_cuda_visible_devices,
            "parent_visible_gpu_ids": parent_visible_ids or [],
            "devices": [],
            "index_kind": "physical",
        }
    if result.returncode != 0 or not result.stdout.strip():
        return {
            "available": False,
            "backend_cuda_visible_devices": parent_cuda_visible_devices,
            "parent_visible_gpu_ids": parent_visible_ids or [],
            "devices": [],
            "index_kind": "physical",
        }

    devices = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue

        try:
            idx = int(parts[0])
        except (ValueError, TypeError):
            continue

        if visible_ordinals is not None and idx not in visible_ordinals:
            continue

        devices.append(
            _build_gpu_metrics(
                vram_used_mb = _parse_smi_value(parts[3]),
                vram_total_mb = _parse_smi_value(parts[4]),
                power_draw = _parse_smi_value(parts[5]),
                power_limit = _parse_smi_value(parts[6]),
                index = idx,
                index_kind = "physical",
                visible_ordinal = (
                    visible_ordinals[idx]
                    if visible_ordinals is not None
                    else len(devices)
                ),
                gpu_utilization_pct = _parse_smi_value(parts[1]),
                temperature_c = _parse_smi_value(parts[2]),
            )
        )

    return {
        "available": len(devices) > 0,
        "backend_cuda_visible_devices": parent_cuda_visible_devices,
        "parent_visible_gpu_ids": parent_visible_ids or [],
        "devices": devices,
        "index_kind": "physical",
    }