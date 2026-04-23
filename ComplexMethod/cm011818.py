def max_pool_checks(
    x, kernel_size, stride, padding, dilation, n_dim, *, assert_fallback=None
):
    if padding == 0:
        padding = [0] * n_dim
    if dilation == 1:
        dilation = [1] * n_dim
    if not stride:
        stride = kernel_size

    kernel_size = pad_listlike(kernel_size, n_dim)
    stride = pad_listlike(stride, n_dim)
    padding = pad_listlike(padding, n_dim)
    dilation = pad_listlike(dilation, n_dim)

    assert isinstance(x, TensorBox)
    assert len(kernel_size) == n_dim
    assert len(stride) == n_dim
    assert len(padding) == n_dim
    assert len(dilation) == n_dim
    assert len(x.get_size()) in (n_dim + 1, n_dim + 2)

    use_fallback = should_fallback_max_pool_with_indices(kernel_size, n_dim=n_dim)
    if assert_fallback is not None:
        assert use_fallback == assert_fallback

    return kernel_size, stride, padding, dilation, use_fallback