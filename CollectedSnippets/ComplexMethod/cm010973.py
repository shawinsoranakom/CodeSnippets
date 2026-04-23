def _broadcast_tensors(
    full_state_dict: dict[str, Any],
    local_state_dict: dict[str, Any],
    keys: list[str],
    device: torch.device,
    pg: dist.ProcessGroup | None = None,
) -> None:
    if pg is None:
        pg = dist.distributed_c10d._get_default_group()
    pg_device = (
        device
        if device.type in {pg_device.type for pg_device in pg._device_types}
        else pg._device_types[0]
    )

    tensors: list[torch.Tensor] = []
    for key in keys:
        if dist.get_rank() == 0:
            full_state = full_state_dict[key]
            if not isinstance(full_state, torch.Tensor):
                raise AssertionError("full_state must be a torch.Tensor")
            full_tensor = full_state.detach().to(pg_device)
        else:
            tensor_info = full_state_dict[key]
            full_tensor = torch.empty(
                size=tensor_info.size,
                device=pg_device,
                dtype=tensor_info.dtype,
            )

        tensors.append(full_tensor)

        if (local_state := local_state_dict.get(key)) is None:
            continue

        local_state_dict[key] = (
            (local_state, full_tensor)
            if isinstance(local_state, DTensor)
            else full_tensor
        )

    if len(tensors) > 1:
        dist._broadcast_coalesced(pg, tensors, 500, 0)
    else:
        dist.broadcast(tensors[0], src=0, group=pg)

    if pg_device != device:
        for key, full_tensor in zip(keys, tensors):
            if (local_state := local_state_dict.get(key)) is not None:
                local_state_dict[key] = (
                    (local_state[0], full_tensor.to(device))
                    if (
                        isinstance(local_state, tuple)
                        and isinstance(local_state[0], DTensor)
                    )
                    else full_tensor.to(device)
                )

    _distribute_tensors(local_state_dict, keys, device, pg)