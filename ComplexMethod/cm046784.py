def get_backend_visible_gpu_info() -> Dict[str, Any]:
    device = get_device()
    if device in (DeviceType.CUDA, DeviceType.XPU):
        parent_visible_ids = get_parent_visible_gpu_ids()
        # Try native SMI tool first (nvidia-smi for NVIDIA, skipped for ROCm)
        if device == DeviceType.CUDA and not IS_ROCM:
            try:
                from . import nvidia

                parent_visible_spec = _get_parent_visible_gpu_spec()
                result = nvidia.get_backend_visible_gpu_info(
                    parent_visible_spec["numeric_ids"],
                    parent_visible_spec["raw"],
                )
                if result.get("available"):
                    result["backend"] = _backend_label(device)
                    return result
            except Exception as e:
                logger.warning("Backend GPU visibility query failed: %s", e)

        # Torch fallback (AMD ROCm, Intel XPU, nvidia-smi missing/failed)
        # When parent_visible_ids is empty (UUID/MIG mask), enumerate by
        # torch ordinal so the UI still shows devices.
        if parent_visible_ids:
            torch_indices = parent_visible_ids
            index_kind = "physical"
        else:
            visible_count = _torch_get_physical_gpu_count() or 0
            torch_indices = list(range(visible_count))
            index_kind = "relative"
        torch_devices = _torch_get_per_device_info(torch_indices)
        if torch_devices:
            devices = [
                {
                    "index": td["index"],
                    "index_kind": index_kind,
                    "visible_ordinal": td["visible_ordinal"],
                    "name": td["name"],
                    "memory_total_gb": td["total_gb"],
                }
                for td in torch_devices
            ]
            return {
                "available": True,
                "backend": _backend_label(device),
                "backend_cuda_visible_devices": _backend_visible_devices_env(),
                "parent_visible_gpu_ids": parent_visible_ids,
                "devices": devices,
                "index_kind": index_kind,
            }

        return {
            "available": False,
            "backend": _backend_label(device),
            "backend_cuda_visible_devices": _backend_visible_devices_env(),
            "parent_visible_gpu_ids": parent_visible_ids,
            "devices": [],
            "index_kind": "physical",
        }

    if device == DeviceType.MLX:
        mem = get_gpu_memory_info()
        if not mem.get("available"):
            return {
                "available": False,
                "backend": _backend_label(device),
                "backend_cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "parent_visible_gpu_ids": [],
                "devices": [],
                "index_kind": "relative",
            }
        return {
            "available": True,
            "backend": _backend_label(device),
            "backend_cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "parent_visible_gpu_ids": [0],
            "devices": [
                {
                    "index": 0,
                    "index_kind": "relative",
                    "visible_ordinal": 0,
                    "name": mem.get("device_name", "MLX"),
                    "memory_total_gb": round(mem.get("total_gb", 0), 2),
                }
            ],
            "index_kind": "relative",
        }

    return {
        "available": False,
        "backend": _backend_label(device),
        "backend_cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "parent_visible_gpu_ids": [],
        "devices": [],
        "index_kind": "relative",
    }