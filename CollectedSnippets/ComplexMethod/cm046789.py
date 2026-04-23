def get_backend_visible_gpu_info(
    parent_visible_ids: Optional[list[int]],
    backend_cuda_visible_devices: Optional[str],
) -> dict[str, Any]:
    # When parent_visible_ids is None (UUID/MIG mask), we cannot safely
    # map nvidia-smi rows to the process's visible devices.
    if parent_visible_ids is None:
        return {
            "available": False,
            "backend_cuda_visible_devices": backend_cuda_visible_devices,
            "parent_visible_gpu_ids": [],
            "devices": [],
            "index_kind": "unresolved",
        }
    visible_ordinals = _visible_ordinal_map(parent_visible_ids)
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output = True,
            text = True,
            timeout = 10,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning("nvidia-smi query failed in get_backend_visible_gpu_info: %s", e)
        return {
            "available": False,
            "backend_cuda_visible_devices": backend_cuda_visible_devices,
            "parent_visible_gpu_ids": parent_visible_ids or [],
            "devices": [],
            "index_kind": "physical",
        }
    if result.returncode != 0:
        return {
            "available": False,
            "backend_cuda_visible_devices": backend_cuda_visible_devices,
            "parent_visible_gpu_ids": parent_visible_ids or [],
            "devices": [],
            "index_kind": "physical",
        }

    devices = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            idx = int(parts[0])
        except (ValueError, TypeError):
            continue
        if visible_ordinals is not None and idx not in visible_ordinals:
            continue
        # Use split with limit to handle GPU names containing commas
        name = parts[1] if len(parts) == 3 else ", ".join(parts[1:-1])
        try:
            mem_total_mb = int(parts[-1])
        except (ValueError, TypeError):
            continue
        devices.append(
            {
                "index": idx,
                "index_kind": "physical",
                "visible_ordinal": (
                    visible_ordinals[idx]
                    if visible_ordinals is not None
                    else len(devices)
                ),
                "name": name,
                "memory_total_gb": round(mem_total_mb / 1024, 2),
            }
        )

    return {
        "available": len(devices) > 0,
        "backend_cuda_visible_devices": backend_cuda_visible_devices,
        "parent_visible_gpu_ids": parent_visible_ids or [],
        "devices": devices,
        "index_kind": "physical",
    }