def _broadcast_state_dict(
    full_state_dict: dict[str, Any],
    local_state_dict: dict[str, Any],
    device: torch.device,
    pg: dist.ProcessGroup | None = None,
    strict: bool = False,
    cpu_offload: bool = False,
) -> None:
    # Broadcast from rank0's `full_state_dict` to all ranks' `local_state_dict`.
    # If strict is True, any keys in `local_state_dict` but not in `full_state_dict`
    # will be removed from `local_state_dict`.
    ret = {}
    if dist.get_rank() == 0:
        for key, value in full_state_dict.items():
            if not torch.is_tensor(value):
                ret[key] = value
            elif value.dim() == 0:
                ret[key] = value.cpu()
            else:
                ret[key] = _TensorInfo(value.size(), value.dtype)

    broadcast_list = [ret]
    dist.broadcast_object_list(broadcast_list, src=0, group=pg)
    ret = broadcast_list[0]
    # Gather values
    keys = []
    local_state_dict_keys = set(local_state_dict.keys())
    global_keys = set()
    for key, value in ret.items():
        global_keys.add(key)
        if not isinstance(value, _TensorInfo):
            if key in local_state_dict:
                local_state_dict[key] = value
            continue

        if dist.get_rank() == 0:
            ret[key] = full_state_dict[key]

        keys.append(key)
        # Broadcast every tensor to avoid OOM for now.
        if len(keys) >= 1:
            _broadcast_tensors(ret, local_state_dict, keys, device, pg)
            if cpu_offload:
                for key in keys:
                    local_state_dict[key] = local_state_dict[key].cpu()
            keys.clear()

    if strict:
        if missing_keys := (local_state_dict_keys - global_keys):
            for key in missing_keys:
                local_state_dict.pop(key)

    if keys:
        _broadcast_tensors(ret, local_state_dict, keys, device, pg)
        if cpu_offload:
            for key in keys:
                local_state_dict[key] = local_state_dict[key].cpu()