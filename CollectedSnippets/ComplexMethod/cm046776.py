def get_gpu_memory_info() -> Dict[str, Any]:
    """
    Get GPU memory information.
    Supports CUDA (NVIDIA), MLX (Apple Silicon), and CPU-only environments.
    """
    device = get_device()

    # ---- CUDA path ----
    if device == DeviceType.CUDA:
        try:
            import torch

            idx = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(idx)

            total = props.total_memory
            allocated = torch.cuda.memory_allocated(idx)
            reserved = torch.cuda.memory_reserved(idx)

            return {
                "available": True,
                "backend": _backend_label(device),
                "device": idx,
                "device_name": props.name,
                "total_gb": total / (1024**3),
                "allocated_gb": allocated / (1024**3),
                "reserved_gb": reserved / (1024**3),
                "free_gb": (total - allocated) / (1024**3),
                "utilization_pct": (allocated / total) * 100,
            }
        except Exception as e:
            logger.error(f"Error getting CUDA GPU info: {e}")
            return {
                "available": False,
                "backend": _backend_label(device),
                "error": str(e),
            }

    # ---- XPU path (Intel GPU) ----
    if device == DeviceType.XPU:
        try:
            import torch

            idx = torch.xpu.current_device()
            props = torch.xpu.get_device_properties(idx)

            total = props.total_memory
            allocated = torch.xpu.memory_allocated(idx)
            reserved = torch.xpu.memory_reserved(idx)

            return {
                "available": True,
                "backend": _backend_label(device),
                "device": idx,
                "device_name": props.name,
                "total_gb": total / (1024**3),
                "allocated_gb": allocated / (1024**3),
                "reserved_gb": reserved / (1024**3),
                "free_gb": (total - allocated) / (1024**3),
                "utilization_pct": (allocated / total) * 100,
            }
        except Exception as e:
            logger.error("Error getting XPU GPU info: %s", e)
            return {
                "available": False,
                "backend": _backend_label(device),
                "error": str(e),
            }

    # ---- MLX path (Apple Silicon) ----
    if device == DeviceType.MLX:
        try:
            import mlx.core as mx
            import psutil

            # MLX uses unified memory — report system memory as the pool
            total = psutil.virtual_memory().total
            # MLX doesn't expose per-process GPU allocation; report 0 as allocated
            allocated = 0

            return {
                "available": True,
                "backend": _backend_label(device),
                "device": 0,
                "device_name": f"Apple Silicon ({platform.processor() or platform.machine()})",
                "total_gb": total / (1024**3),
                "allocated_gb": allocated / (1024**3),
                "reserved_gb": 0,
                "free_gb": (total - allocated) / (1024**3),
                "utilization_pct": (allocated / total) * 100 if total else 0,
            }
        except Exception as e:
            logger.error(f"Error getting MLX GPU info: {e}")
            return {
                "available": False,
                "backend": _backend_label(device),
                "error": str(e),
            }

    # ---- CPU-only ----
    return {"available": False, "backend": "cpu"}