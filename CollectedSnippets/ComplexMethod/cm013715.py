def data_parallel(
    module: Module,
    inputs: Any,
    device_ids: Sequence[int | torch.device] | None = None,
    output_device: int | torch.device | None = None,
    dim: int = 0,
    module_kwargs: Any | None = None,
) -> torch.Tensor:
    r"""Evaluate module(input) in parallel across the GPUs given in device_ids.

    This is the functional version of the DataParallel module.

    Args:
        module (Module): the module to evaluate in parallel
        inputs (Tensor): inputs to the module
        device_ids (list of int or torch.device): GPU ids on which to replicate module
        output_device (list of int or torch.device): GPU location of the output  Use -1 to indicate the CPU.
            (default: device_ids[0])
    Returns:
        a Tensor containing the result of module(input) located on
        output_device
    """
    if not isinstance(inputs, tuple):
        inputs = (inputs,) if inputs is not None else ()

    device_type = _get_available_device_type()

    if device_type is None:
        raise RuntimeError("device type could not be determined")

    if device_ids is None:
        device_ids = _get_all_device_indices()

    if device_ids is None:
        raise RuntimeError("no available devices were found")

    if output_device is None:
        output_device = device_ids[0]

    device_ids = [_get_device_index(x, True) for x in device_ids]
    output_device = _get_device_index(output_device, True)
    # pyrefly: ignore [bad-argument-type, no-matching-overload]
    src_device_obj = torch.device(device_type, device_ids[0])

    # pyrefly: ignore [bad-argument-type]
    for t in chain(module.parameters(), module.buffers()):
        if t.device != src_device_obj:
            raise RuntimeError(
                "module must have its parameters and buffers "
                f"on device {src_device_obj} (device_ids[0]) but found one of "
                f"them on device: {t.device}"
            )

    inputs, module_kwargs = scatter_kwargs(inputs, module_kwargs, device_ids, dim)
    # for module without any inputs, empty list and dict will be created
    # so the module can be executed on one device which is the first one in device_ids
    if not inputs and not module_kwargs:
        inputs = ((),)
        module_kwargs = ({},)

    if module_kwargs is None:
        raise AssertionError("module_kwargs should not be None after scatter_kwargs")

    if len(device_ids) == 1:
        return module(*inputs[0], **module_kwargs[0])
    used_device_ids = device_ids[: len(inputs)]
    replicas = replicate(module, used_device_ids)
    outputs = parallel_apply(replicas, inputs, module_kwargs, used_device_ids)
    return gather(outputs, output_device, dim)