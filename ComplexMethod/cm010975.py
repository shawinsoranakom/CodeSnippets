def _distribute_state_dict(
    full_state_dict: dict[str, Any],
    local_state_dict: dict[str, Any],
    device: torch.device,
    pg: dist.ProcessGroup | None = None,
) -> None:
    # Full_state_dict = True, broadcast_from_rank0 = False here. Each rank has
    # full_state_dict. Skip the broadcast in ``_broadcast_state_dict`` and
    # distribute tensors in each rank
    for key, value in full_state_dict.items():
        if key not in full_state_dict:
            continue
        if not torch.is_tensor(value):
            local_state_dict[key] = value
        elif value.dim() == 0:
            local_state_dict[key] = value.cpu()
        else:
            if not isinstance(value, torch.Tensor):
                raise AssertionError("value must be a torch.Tensor")
            local_state = local_state_dict.get(key)
            if local_state is None:
                continue
            elif isinstance(local_state, DTensor):
                local_state_dict[key] = distribute_tensor(
                    value.detach().to(device),
                    local_state.device_mesh,
                    local_state.placements,
                )
            else:
                local_state_dict[key] = value.detach().to(device)