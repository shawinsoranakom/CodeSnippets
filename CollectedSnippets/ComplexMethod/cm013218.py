def reference_group_norm(inp: npt.NDArray, num_groups: int, weight=None, bias=None, eps=1e-5):
    inp_view = inp
    if np.prod(inp.shape) != 0:
        inp_view = inp.reshape((inp.shape[0], num_groups, -1))
    mean = inp_view.mean(axis=-1, keepdims=True)
    var = inp_view.var(axis=-1, ddof=0, keepdims=True)
    Y = (inp_view - mean) / np.sqrt(var + eps)
    Y = Y.reshape(inp.shape)
    if weight is not None:
        # weight is a vector of length equal to the channel
        if len(Y.shape) > 2:
            weight = np.expand_dims(weight, [0] + [idx + 2 for idx in range(inp.ndim - 2)])
        Y = Y * weight
    if bias is not None:
        # bias is a vector of length equal to the channel
        if len(Y.shape) > 2:
            bias = np.expand_dims(bias, [0] + [idx + 2 for idx in range(inp.ndim - 2)])
        Y = Y + bias
    return Y