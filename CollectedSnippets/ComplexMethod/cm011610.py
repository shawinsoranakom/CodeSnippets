def _internal_new_from_data(
    options,
    scalar_type,
    device_opt,
    data,
    copy_variables,
    copy_numpy,
    type_inference,
    pin_memory=False,
):
    if isinstance(data, torch.Tensor):
        torch._check(
            not pin_memory, lambda: "Can't pin tensor constructed from a variable"
        )
        var = data
        if copy_variables:
            var = var.detach()
        inferred_scalar_type = var.dtype if type_inference else scalar_type
        device = device_opt if device_opt is not None else var.device
        return var.to(
            device=device,
            dtype=inferred_scalar_type,
            non_blocking=False,
            copy=copy_variables,
        )

    # TODO
    if hasattr(data, "__cuda_array_interface__"):
        return NotImplemented

    # TODO: test for numpy input with PyArray_Check

    device = device_opt if device_opt is not None else options["device"]
    inferred_scalar_type = _infer_scalar_type(data) if type_inference else scalar_type

    # NB: Don't need to avoid tracing, as we aren't going to do any manual
    # pointer filling tricks
    if _isStorage(data):
        return NotImplemented
    else:
        if torch.device(device).type == "meta":
            return NotImplemented

        # In the C implementation, we would directly start poking the memory
        # of a freshly allocated CPU tensor.  Here, we're going to do an
        # alternate, heinously slow implementation: turn each individual
        # scalar into a tensor, and then repeatedly cat them together
        tensor = _recursive_build(inferred_scalar_type, data)

        tensor = tensor.to(device, inferred_scalar_type, non_blocking=False, copy=False)

    # NB: lift_fresh is not needed, because we built the tensor from scalars
    # guaranteeing a fresh tensor in this case
    return tensor