def meta_select(
    fake_mode: FakeTensorMode,
    func: OpOverload,
    self: FakeTensor,
    dim: int,
    index: IntLikeType,
) -> FakeTensor:
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if self.is_sparse:
        return NotImplemented

    ndim = self.dim()
    torch._check_index(
        ndim != 0,
        lambda: "select() cannot be applied to a 0-dim tensor.",
    )

    dim = dim if dim >= 0 else dim + ndim
    size = self.size(dim)

    new_size = list(self.size())
    new_stride = list(self.stride())

    new_storage_offset = None
    if guard_or_false(index >= 0):
        new_storage_offset = self.storage_offset() + index * new_stride[dim]
    elif guard_or_false(index < 0):
        new_storage_offset = self.storage_offset() + (index + size) * new_stride[dim]

    if new_storage_offset is None:
        if fake_mode.shape_env is None or (
            not fake_mode.shape_env.allow_scalar_outputs
            and not fake_mode.allow_scalar_outputs
        ):
            raise DataDependentOutputException(func)

        # index is data-dependent, we do not know which index we are accessing it could be index or index+size!
        # we assign a new data-dependent symbol for the storage offset.
        new_storage_offset = fake_mode.shape_env.create_unbacked_symint()

    del new_size[dim]
    del new_stride[dim]
    if new_storage_offset is None:
        raise AssertionError("new_storage_offset must not be None")
    # pyrefly: ignore[bad-return]
    return self.as_strided(new_size, new_stride, new_storage_offset)