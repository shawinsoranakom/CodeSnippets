def slice_forward(
    # Tensor(a) self, int dim=0, SymInt? start=None, SymInt? end=None, SymInt step=1
    self: Tensor,
    dim: int = 0,
    start: int | None = None,
    end: int | None = None,
    step: int = 1,
):
    from torch.fx.experimental.symbolic_shapes import statically_known_true

    ndim = self.dim()
    if ndim == 0:
        raise RuntimeError("slice() cannot be applied to a 0-dim tensor.")
    dim = utils.canonicalize_dim(self.dim(), dim)
    sizes = list(self.size())
    strides = list(self.stride())

    if step <= 0:
        raise RuntimeError("slice step must be positive")

    start_val = start if start is not None else 0
    end_val = end if end is not None else sys.maxsize  # 2^63 - 1

    if start_val < 0:
        start_val += sizes[dim]

    if end_val < 0:
        end_val += sizes[dim]

    if start_val < 0:
        start_val = 0
    elif start_val > sizes[dim]:
        start_val = sizes[dim]

    if statically_known_true(end_val == sys.maxsize):
        end_val = sizes[dim]
    elif end_val < start_val:
        end_val = start_val
    elif end_val > sizes[dim]:
        end_val = sizes[dim]

    storage_offset = self.storage_offset() + start_val * strides[dim]
    len = end_val - start_val
    sizes[dim] = (len + step - 1) // step
    strides[dim] *= step

    if self.is_quantized:
        raise NotImplementedError(
            "Slice decomposition for quantized tensors aren't implemented"
        )
    else:
        return self.as_strided(sizes, strides, storage_offset)