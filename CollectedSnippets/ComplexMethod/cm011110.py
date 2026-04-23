def _init_device_handle(
    state: _FSDPState,
    module: nn.Module,
    ignored_params: set[nn.Parameter],
    device_id: int | torch.device | None,
) -> _FSDPState:
    """
    Determine device handle used for initializing FSDP.

    If a device is specified by ``device_id``,
    then returns device handle corresponds to that device type. Otherwise, If the
    module is already on a non-CPU device, then the device type is that non-CPU device type.
    If the module is on CPU or meta, then the device type is the current accelerator device.
    See the :ref:`Accelerators<accelerators>` for details.


    This method will be called once ignored parameters was determined, as the device handle maybe needed
    for other initialization.
    """
    determined_device = None
    if device_id is not None:
        determined_device = (
            device_id
            if isinstance(device_id, torch.device)
            else torch.device(device_id)
        )
    if determined_device is None:
        for param in _get_orig_params(module, ignored_params):
            if param.device.type in {"cpu", "meta"}:
                continue
            if determined_device is None:
                determined_device = param.device
            else:
                if param.device.type != determined_device.type:
                    raise RuntimeError(
                        f"FSDP does not support modules with different device types "
                        f"but got params on {determined_device.type} and {param.device.type}"
                    )
        determined_device = determined_device or torch._C._get_accelerator()
        if determined_device.type == "cpu":
            raise RuntimeError(
                "FSDP needs a non-CPU accelerator device, but no accelerator device is detected."
            )

    state._device_handle = _FSDPDeviceHandle.from_device(determined_device)
    return state