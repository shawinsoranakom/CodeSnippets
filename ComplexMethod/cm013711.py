def reduce_add(inputs, destination=None):
    """Sum tensors from multiple GPUs.

    All inputs should have matching shapes, dtype, and layout. The output tensor
    will be of the same shape, dtype, and layout.

    Args:
        inputs (Iterable[Tensor]): an iterable of tensors to add.
        destination (int, optional): a device on which the output will be
            placed (default: current device).

    Returns:
        A tensor containing an elementwise sum of all inputs, placed on the
        :attr:`destination` device.
    """
    destination = _get_device_index(destination, optional=True)
    input_size = inputs[0].size()
    root_index = None  # index of input tensor that already is on the correct device
    for i, inp in enumerate(inputs):
        if inp.device.type == "cpu":
            raise AssertionError(
                f"reduce_add expects all inputs to be on GPUs, but input {i} is on CPU"
            )
        if inp.get_device() == destination:
            root_index = i
        if inp.size() != input_size:
            got = "x".join(str(x) for x in inp.size())
            expected = "x".join(str(x) for x in input_size)
            raise ValueError(
                f"input {i} has invalid size: got {got}, but expected {expected}"
            )
    if root_index is None:
        raise RuntimeError(
            "reduce_add expects destination to be on the same GPU with one of the tensors"
        )

    if len(inputs) == 1:
        return inputs[0]

    if nccl.is_available(inputs):
        result = torch.empty_like(inputs[root_index])
        nccl.reduce(inputs, output=result, root=root_index)
    else:
        destination_device = torch.device(inputs[root_index].device.type, destination)
        nonroot = [t for i, t in enumerate(inputs) if i != root_index]
        # make a new tensor w/o clone
        result = inputs[root_index] + nonroot[0].to(
            device=destination_device, non_blocking=True
        )
        for other in nonroot[1:]:
            result.add_(other.to(device=destination_device, non_blocking=True))
    return result