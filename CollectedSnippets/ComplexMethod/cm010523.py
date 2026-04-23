def TensorMeta(
    tensorlike: NumberType | torch.Tensor | None = None,
    *,
    shape: ShapeType | None = None,
    strides: StrideType | None = None,
    dtype: torch.dtype | None = None,
    device: torch.device | str | None = None,
):
    if isinstance(tensorlike, Number):
        if shape and not isinstance(shape, Sequence):
            raise AssertionError(
                f"shape must be None or a Sequence for Number input, got {type(shape)}"
            )
        if strides and not isinstance(strides, Sequence):
            raise AssertionError(
                f"strides must be None or a Sequence for Number input, got {type(strides)}"
            )
        inferred_shape: tuple[int, ...] = ()
        inferred_strides: tuple[int, ...] = ()
        inferred_dtype = type_to_dtype(type(tensorlike))
        inferred_device = torch.device("cpu")
        # TODO: This looks wrong, a number that is wrapped into a tensor
        # needs to behave differently than a scalar tensor for type
        # promotion purposes
    elif tensorlike is not None:
        if not isinstance(tensorlike, torch.Tensor):
            raise AssertionError(
                f"tensorlike must be torch.Tensor, got {type(tensorlike)}"
            )  # mypy
        inferred_shape = tuple(tensorlike.shape)
        inferred_strides = tuple(tensorlike.stride())
        inferred_dtype = tensorlike.dtype
        inferred_device = tensorlike.device
    else:
        # If no tensorlike "example" is given then all metadata
        # must be provided explicitly
        if shape is None:
            raise AssertionError("shape must be provided when tensorlike is None")
        if strides is None:
            raise AssertionError("strides must be provided when tensorlike is None")
        if dtype is None:
            raise AssertionError("dtype must be provided when tensorlike is None")
        if device is None:
            raise AssertionError("device must be provided when tensorlike is None")

    shape = inferred_shape if shape is None else tuple(shape)  # type: ignore[possibly-undefined]
    strides = inferred_strides if strides is None else tuple(strides)  # type: ignore[possibly-undefined]
    dtype = inferred_dtype if dtype is None else dtype  # type: ignore[possibly-undefined]
    device = inferred_device if device is None else device  # type: ignore[possibly-undefined]

    if isinstance(device, str):
        device = torch.device(device)

    return torch.empty_strided(shape, strides, dtype=dtype, device=device)