def get_visible_gpu_utilization() -> Dict[str, Any]:
    device = get_device()

    if device == DeviceType.CUDA:
        parent_visible_spec = _get_parent_visible_gpu_spec()
        result = _smi_query(
            "get_visible_gpu_utilization",
            parent_visible_spec["numeric_ids"],
            parent_cuda_visible_devices = parent_visible_spec["raw"],
        )
        if result is not None:
            result["backend"] = _backend_label(device)
            return result

    # Torch-based fallback for CUDA (nvidia-smi unavailable, AMD ROCm) and XPU (Intel)
    if device in (DeviceType.CUDA, DeviceType.XPU):
        parent_ids = get_parent_visible_gpu_ids()
        # When parent_visible_ids is empty (UUID/MIG mask or no CVD set),
        # enumerate torch-visible ordinals so the UI still shows devices.
        if parent_ids:
            torch_indices = parent_ids
            index_kind = "physical"
        else:
            visible_count = _torch_get_physical_gpu_count() or 0
            torch_indices = list(range(visible_count))
            index_kind = "relative"
        torch_devices = _torch_get_per_device_info(torch_indices)
        if torch_devices:
            devices = []
            for td in torch_devices:
                total = td["total_gb"]
                used = td["used_gb"]
                devices.append(
                    {
                        "index": td["index"],
                        "index_kind": index_kind,
                        "visible_ordinal": td["visible_ordinal"],
                        "gpu_utilization_pct": None,
                        "temperature_c": None,
                        "vram_used_gb": used,
                        "vram_total_gb": total,
                        "vram_utilization_pct": round((used / total) * 100, 1)
                        if total > 0
                        else None,
                        "power_draw_w": None,
                        "power_limit_w": None,
                        "power_utilization_pct": None,
                    }
                )
            return {
                "available": True,
                "backend": _backend_label(device),
                "parent_visible_gpu_ids": parent_ids,
                "devices": devices,
                "index_kind": index_kind,
            }

    if device == DeviceType.MLX:
        mem = get_gpu_memory_info()
        if not mem.get("available"):
            return {
                "available": False,
                "backend": _backend_label(device),
                "parent_visible_gpu_ids": [],
                "devices": [],
                "index_kind": "relative",
            }
        return {
            "available": True,
            "backend": _backend_label(device),
            "parent_visible_gpu_ids": [0],
            "devices": [
                {
                    "index": 0,
                    "index_kind": "relative",
                    "visible_ordinal": 0,
                    "gpu_utilization_pct": None,
                    "temperature_c": None,
                    "vram_used_gb": round(mem.get("allocated_gb", 0), 2),
                    "vram_total_gb": round(mem.get("total_gb", 0), 2),
                    "vram_utilization_pct": round(mem.get("utilization_pct", 0), 1),
                    "power_draw_w": None,
                    "power_limit_w": None,
                    "power_utilization_pct": None,
                }
            ],
            "index_kind": "relative",
        }

    return {
        "available": False,
        "backend": _backend_label(device),
        "parent_visible_gpu_ids": [],
        "devices": [],
        "index_kind": "relative",
    }