def slice_forward(
    fake_mode: FakeTensorMode,
    func: OpOverload,
    self: FakeTensor,
    dim: int = 0,
    start: int | None = None,
    end: int | None = None,
    step: int = 1,
) -> FakeTensor:
    from torch.fx.experimental.symbolic_shapes import (
        guard_or_false,
        statically_known_true,
    )

    shape_env = fake_mode.shape_env
    ndim = self.dim()
    if ndim == 0:
        raise RuntimeError("slice() cannot be applied to a 0-dim tensor.")
    dim = canonicalize_dim(self.dim(), dim)
    sizes = list(self.size())
    strides = list(self.stride())

    if step <= 0:
        raise RuntimeError("slice step must be positive")

    # start, end
    start_index = 0 if start is None else _compute_slice_index(sizes[dim], start)
    end_index = (
        sizes[dim]
        if statically_known_true(end == sys.maxsize) or end is None
        else _compute_slice_index(sizes[dim], end)
    )

    # size
    new_size: IntLikeType | None = None
    if start_index is not None and end_index is not None:
        if guard_or_false(end_index >= start_index):
            new_size = (end_index - start_index + step - 1) // step
        elif guard_or_false(start_index >= end_index):
            new_size = 0
        else:
            # Both indices are resolved but we can't statically determine their
            # ordering (e.g., when they involve Min/Max). Compute the size via
            # max(end - start, 0) to avoid creating an unbacked symint.
            diff = torch.sym_max(end_index - start_index, 0)
            new_size = (diff + step - 1) // step

    # create unbacked if case unknown
    if new_size is None:
        if shape_env is None:
            raise AssertionError("Must have shape_env to create symint")
        new_size = shape_env.create_unbacked_symint()
        torch._check(new_size >= 0)
        torch._check(new_size <= sizes[dim])

    # stride
    new_stride = strides[dim] * step

    # storage offset
    if start_index is not None:
        storage_offset = self.storage_offset() + start_index * strides[dim]
    else:
        if shape_env is None:
            raise AssertionError("Must have shape_env to create symint")
        storage_offset = shape_env.create_unbacked_symint()
        torch._check(storage_offset >= 0)

    sizes[dim] = new_size  # type: ignore[unsupported-operation]
    strides[dim] = new_stride
    if self.is_quantized:
        raise NotImplementedError(
            "Slice decomposition for quantized tensors aren't implemented"
        )
    else:
        return self.as_strided(sizes, strides, storage_offset)