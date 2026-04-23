def slice(
    self: list[int], dim: int, start: Optional[int], end: Optional[int], step: int
):
    ndim = len(self)
    if ndim == 0:
        raise AssertionError("Cannot slice a 0-dimensional tensor")
    dim = maybe_wrap_dim(dim, ndim)
    start_val = start if start is not None else 0
    end_val = end if end is not None else max_int()
    if step <= 0:
        raise AssertionError(f"Expected step > 0, but got {step}")
    if start_val == max_int():
        start_val = 0
    if start_val < 0:
        start_val += self[dim]
    if end_val < 0:
        end_val += self[dim]
    if start_val < 0:
        start_val = 0
    elif start_val > self[dim]:
        start_val = self[dim]
    if end_val < start_val:
        end_val = start_val
    elif end_val >= self[dim]:
        end_val = self[dim]
    slice_len = end_val - start_val
    out = _copy(self)
    out[dim] = (slice_len + step - 1) // step
    return out