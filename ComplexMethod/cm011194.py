def _compute_local_tensor_meta(
    local_tensors: dict[int, torch.Tensor],
) -> tuple[
    list[torch.SymInt | int],
    list[torch.SymInt | int],
    torch.device,
    torch.dtype,
    torch.layout,
    DispatchKeySet,
]:
    """
    Computes the meta information for a LocalTensor from its local tensors.
    """
    it = iter(local_tensors.values())
    first_local_tensor = next(it)

    first_shape = first_local_tensor.shape
    first_stride = first_local_tensor.stride()
    dtype = first_local_tensor.dtype
    device = first_local_tensor.device
    layout = first_local_tensor.layout

    extra_dispatch_keys = _get_extra_dispatch_keys(first_local_tensor)

    # Assert that all tensors have the same dtype, layout and dispatch keys. Due
    # to uneven sharding, it is possible that tensors will have different shapes.
    for local_tensor in it:
        if dtype != local_tensor.dtype:
            raise AssertionError(
                "Tensors representing LocalTensor shards must have the same dtype"
            )
        if layout != local_tensor.layout:
            raise AssertionError(
                "Tensors representing LocalTensor shards must have the same layout"
            )
        if extra_dispatch_keys != _get_extra_dispatch_keys(local_tensor):
            raise AssertionError(
                "Tensors representing LocalTensor shards must have the "
                "same set of extra dispatch keys"
            )

    # Compute shape/stride.  We allow for non-SPMD'ness here
    local_shapes: dict[int, dict[int, int]] = defaultdict(dict)  # dim => rank => size
    local_strides: dict[int, dict[int, int]] = defaultdict(dict)  # dim => rank => size
    for r, local_tensor in local_tensors.items():
        for d, size in enumerate(local_tensor.shape):
            local_shapes[d][r] = size
            local_strides[d][r] = local_tensor.stride(d)
    shape = [
        (
            first_shape[d]
            if _all_elements_same(list(local_shapes[d].values()))
            else torch.SymInt(LocalIntNode(local_shapes[d]))
        )
        for d in range(len(first_shape))
    ]
    strides = [
        (
            first_stride[d]
            if _all_elements_same(list(local_strides[d].values()))
            else torch.SymInt(LocalIntNode(local_strides[d]))
        )
        for d in range(len(first_shape))
    ]
    return shape, strides, device, dtype, layout, extra_dispatch_keys