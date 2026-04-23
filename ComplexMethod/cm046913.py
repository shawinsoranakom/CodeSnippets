def prepare_device_map():
    rank, world_size = _infer_distributed_ranks()
    distributed = (world_size or 1) > 1 or (rank is not None and rank > 0)
    if not distributed:
        return None, False

    local_rank = 0 if rank is None else rank
    device_map = {"": f"{DEVICE_TYPE_TORCH}:{local_rank}"}
    try:
        if DEVICE_TYPE_TORCH == "cuda":
            torch.cuda.set_device(local_rank)
        elif DEVICE_TYPE_TORCH == "xpu" and hasattr(torch, "xpu"):
            torch.xpu.set_device(local_rank)
    except Exception:
        pass
    return device_map, True