def diagonal(x, offset=0, axis1=0, axis2=1):
    x = get_ov_output(x)
    shape = x.get_partial_shape()
    rank = x.get_partial_shape().rank.get_length()
    if rank is None:
        raise ValueError("`diagonal` requires input tensor with static rank.")
    if rank < 2:
        raise ValueError(
            f"diagonal requires input tensor with rank >= 2.Given rank: {rank}"
        )
    axis1 = canonicalize_axis(axis1, rank)
    axis2 = canonicalize_axis(axis2, rank)
    if axis1 == axis2:
        raise ValueError("`axis1` and `axis2` cannot be the same.")

    perm_order = [axis1, axis2] + [
        i for i in range(rank) if i != axis1 and i != axis2
    ]
    perm_const = ov_opset.constant(perm_order, dtype=Type.i32).output(0)
    x_transposed = ov_opset.transpose(x, perm_const)

    N_dim = shape[axis1]
    M_dim = shape[axis2]
    if not N_dim.is_static or not M_dim.is_static:
        raise ValueError(
            "`diagonal` requires input tensor with static shape for axes "
            f"`axis1` ({axis1}) and `axis2` ({axis2})."
        )
    N = N_dim.get_length()
    M = M_dim.get_length()
    if offset >= 0:
        L = np.minimum(N, M - offset) if (M - offset) > 0 else 0
        indices = [[i, i + offset] for i in range(L)]
    else:
        L = np.minimum(N + offset, M) if (N + offset) > 0 else 0
        indices = [[i - offset, i] for i in range(L)]

    indices = np.array(indices, dtype=np.int32).reshape(L, 2)
    indices_const = ov_opset.constant(indices, dtype=Type.i32).output(0)

    diag_gathered = ov_opset.gather_nd(x_transposed, indices_const)

    out_rank = rank - 1
    out_perm_order = list(range(1, out_rank)) + [0]
    out_perm_const = ov_opset.constant(out_perm_order, dtype=Type.i32).output(0)

    final_output = ov_opset.transpose(diag_gathered, out_perm_const)
    return OpenVINOKerasTensor(final_output.output(0))