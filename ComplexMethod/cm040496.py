def repeat(x, repeats, axis=None):
    x = get_ov_output(x)
    const_0 = ov_opset.constant(0, Type.i32)
    const_1 = ov_opset.constant(1, Type.i32)
    const_neg_1 = ov_opset.constant([-1], Type.i32)

    if axis is not None and axis < 0:
        axis += len(x.get_partial_shape())

    if axis is None:
        x = ov_opset.reshape(x, const_neg_1, special_zero=False)
        axis = 0

    if isinstance(repeats, np.integer):
        repeats = int(repeats)
    elif (
        isinstance(repeats, np.ndarray)
        and repeats.size == 1
        and repeats.ndim <= 1
    ):
        repeats = int(repeats.item())

    if isinstance(repeats, int):
        dim_len = ov_opset.gather(
            ov_opset.shape_of(x, Type.i32),
            ov_opset.constant([axis], Type.i32),
            const_0,
        )
        dim_len = ov_opset.squeeze(dim_len, ov_opset.constant([0], Type.i32))
        idx_range = ov_opset.range(
            const_0, dim_len, const_1, output_type=Type.i32
        )
        idx_range = ov_opset.unsqueeze(idx_range, const_1)
        tiled = ov_opset.tile(
            idx_range, ov_opset.constant([1, repeats], Type.i32)
        )
        idx = ov_opset.reshape(tiled, const_neg_1, special_zero=False)
        result = ov_opset.gather(x, idx, ov_opset.constant(axis, Type.i32))
        return OpenVINOKerasTensor(result.output(0))
    repeats_tensor = get_ov_output(repeats)
    cumsum = ov_opset.cumsum(repeats_tensor, const_0)
    total = ov_opset.reduce_sum(
        repeats_tensor, ov_opset.constant([0], Type.i32), keep_dims=False
    )
    total = ov_opset.convert(total, Type.i32)
    out_indices = ov_opset.range(const_0, total, const_1, output_type=Type.i32)
    cumsum_unsq = ov_opset.unsqueeze(cumsum, const_0)
    out_indices_unsq = ov_opset.unsqueeze(out_indices, const_1)
    cumsum_unsq = ov_opset.convert(cumsum_unsq, Type.i32)
    mask = ov_opset.greater_equal(out_indices_unsq, cumsum_unsq)
    gather_indices = ov_opset.reduce_sum(
        ov_opset.convert(mask, Type.i32), ov_opset.constant([1], Type.i32)
    )
    result = ov_opset.gather(
        x, gather_indices, ov_opset.constant(axis, Type.i32)
    )
    return OpenVINOKerasTensor(result.output(0))