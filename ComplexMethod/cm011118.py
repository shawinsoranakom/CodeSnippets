def _move_states_to_device(
    params: list[nn.Parameter],
    buffers: list[torch.Tensor],
    device_from_device_id: torch.device | None,
) -> None:
    """
    Move states to the specified device.

    Precondition: ``_check_single_device_module()`` and module's parameters and
    buffers have been materialized if needed.
    """
    if len(params) == 0 and len(buffers) == 0:
        return
    if len(params) > 0:
        current_device = params[0].device
    elif len(buffers) > 0:
        current_device = buffers[0].device
    cpu_device = torch.device("cpu")
    if device_from_device_id is not None:
        # Move the parameters and buffers like the `.data` code path in
        # `nn.Module._apply()`, which underlies `nn.Module.to()`
        for param in params:
            with torch.no_grad():
                param.data = param.to(device_from_device_id)
                if param.grad is not None:
                    param.grad.data = param.grad.to(device_from_device_id)
        for buffer in buffers:
            buffer.data = buffer.to(device_from_device_id)
    elif current_device == cpu_device:  # type: ignore[possibly-undefined]
        _warn_cpu_init()