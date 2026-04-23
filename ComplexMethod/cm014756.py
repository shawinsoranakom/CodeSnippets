def random_nt_from_similar(other, dims=None):
    if dims is None:
        return torch.randn_like(other)
    if len(dims) != other.dim():
        raise AssertionError(
            f"Expected len(dims) == other.dim(), got {len(dims)} vs {other.dim()}"
        )
    if not (dims[0] == -1 or dims[0] == other.size(0)):
        raise AssertionError(
            f"Expected dims[0] == -1 or dims[0] == other.size(0), got {dims[0]}"
        )

    ret_sizes = []
    for t in other.unbind():
        other_size = t.shape
        ret_size = []
        for i, d in enumerate(dims[1:]):
            if d == -1:
                ret_size.append(other_size[i])
            else:
                ret_size.append(d)
        ret_sizes.append(ret_size)

    return torch.nested.nested_tensor(
        [torch.randn(*size) for size in ret_sizes], device=other.device
    )