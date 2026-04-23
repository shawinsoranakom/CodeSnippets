def _view_unbacked_meta(
    a: torch.Tensor,
    shape: ShapeType | tuple[ShapeType],
    size_oblivious_enabled: bool = True,
    allow_copy: bool = False,
) -> torch.Tensor:
    from torch._prims import view_of
    from torch.fx.experimental.symbolic_shapes import guard_or_false, sym_eq

    # Creates a valid shape
    shape = utils.extract_shape_from_varargs(shape, validate=False)

    # Reshape may be given a shape with a -1 length
    # This indicates that the dimension's length should be inferred
    shape = utils.infer_size(shape, a.numel())

    # Special-cases reshaping zero dim tensors
    if a.ndim == 0:
        _a = a
        for length in shape:
            torch._check(length == 1)
            _a = torch._refs.unsqueeze(_a, -1)
        if _a is a:
            return view_of(a)
        else:
            return _a  # type: ignore[return-value]

    # Special-cases reshaping to zero dim tensors
    if len(shape) == 0:
        _a = a
        for length in a.shape:
            torch._check(length == 1)
            _a = torch._refs.squeeze(_a, -1)
        if _a is a:
            return view_of(a)
        else:
            return _a  # type: ignore[return-value]

    shape_numel = reduce(operator.mul, shape, 1)

    torch._check(
        a.numel() == shape_numel,
        lambda: f"Could not reshape a tensor with shape {a.shape} as a tensor with shape {shape}!",
    )

    if len(shape) == len(a.shape) and guard_or_false(sym_eq(shape, a.shape)):
        return view_of(a)

    if is_contiguous_or_false(a) if size_oblivious_enabled else is_contiguous(a):
        strides = make_contiguous_strides_for(shape)
        return a.as_strided(shape, strides)  # type: ignore[return-value]

    new_strides = _compute_stride(
        a.size(), a.stride(), shape, size_oblivious=size_oblivious_enabled
    )

    if new_strides is not None:
        return a.as_strided(shape, new_strides)  # type: ignore[return-value]

    # If we fail to do size oblivious view, and backed_size_oblivious was on,
    # then we redo everything by looking at hints and guarding instead of failing.
    # Also if the expression has unbacked symbols, then we run again with size_oblivious_enabled=False
    # to throw a data dependent error.

    if size_oblivious_enabled and (
        torch.fx.experimental._config.backed_size_oblivious
        or _view_has_unbacked_input(a, shape)
    ):
        return _view_unbacked_meta(
            a, shape, size_oblivious_enabled=False, allow_copy=allow_copy
        )

    # When allow_copy=True (i.e., view_copy), define unbacked semantics
    # as "materialize": clone the input to break aliasing, then reshape.
    if allow_copy:
        strides = make_contiguous_strides_for(shape)
        # pyrefly: ignore[bad-return]
        return a.clone(memory_format=torch.contiguous_format).as_strided(shape, strides)

    msg = f"Cannot view a tensor with shape {a.shape} and strides {a.stride()} as a tensor with shape {shape}!"
    raise ValueError(msg)