def scatter_upon_const_tensor_extra_check(m):
    if not config.optimize_scatter_upon_const_tensor:
        return False
    full_shape = m.kwargs["shape"]
    selector = m.kwargs["selector"]
    dim = m.kwargs["dim"]
    if dim < 0:
        dim += len(full_shape)

    selector_ft = selector.meta["val"]
    assert selector_ft.dim() == len(full_shape)

    for idx, select_sz, full_sz in zip(
        itertools.count(), selector_ft.shape, full_shape
    ):
        if idx == dim:
            continue

        # TODO: the pattern can be updated to support the case that index tensor
        # is shorter. But that will need a more complex condition expression
        # especially for multi-dimensional tensors.
        # Skip it for now.
        if isinstance(full_sz, torch.fx.Node):
            full_sz = full_sz.meta["val"]
        if select_sz < full_sz:
            return False

    # Actually we can support small size larger than 1. It would be a bit
    # tedious. E.g., we load all the index values (not many) and compare
    # them with the position in tensor to decide what value to return.
    return selector_ft.size(dim) == 1