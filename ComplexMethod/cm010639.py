def expand(self: list[int], sizes: list[int]):
    if len(sizes) < len(self):
        raise AssertionError(
            f"Expected len(sizes) ({len(sizes)}) >= len(self) ({len(self)})"
        )
    ndim = len(sizes)
    tensor_dim = len(self)
    if ndim == 0:
        return _copy(sizes)
    out: list[int] = []
    for i in range(ndim):
        offset = ndim - 1 - i
        dim = tensor_dim - 1 - offset
        size = self[dim] if dim >= 0 else 1
        targetSize = sizes[i]
        if targetSize == -1:
            if dim < 0:
                raise AssertionError(f"Expected dim ({dim}) >= 0 when targetSize is -1")
            targetSize = size
        if size != targetSize:
            if size != 1:
                raise AssertionError(
                    f"Expected size ({size}) == 1 when size != targetSize ({targetSize})"
                )
            size = targetSize
        out.append(size)
    return out