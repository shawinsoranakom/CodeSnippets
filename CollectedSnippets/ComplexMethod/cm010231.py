def semi_sparse_to(func, types, args, kwargs=None) -> torch.Tensor:
    self = args[0]
    remaining_args = args[1:]
    kwargs = kwargs or {}

    # Determine the target device from args/kwargs
    device = None
    if remaining_args:
        first_arg = remaining_args[0]
        if isinstance(first_arg, (torch.device, str)):
            try:
                device = torch.device(first_arg)
            except RuntimeError:
                pass
    if "device" in kwargs:
        device = torch.device(kwargs["device"])

    if device is not None and device.type == "cpu":
        dense = self.to_dense()
        return func(dense, *remaining_args, **kwargs)

    raise NotImplementedError(
        f"`to()` with args={remaining_args}, kwargs={kwargs} is not implemented "
        "for SparseSemiStructuredTensor. Only `to('cpu')` is supported currently."
    )