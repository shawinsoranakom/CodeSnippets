def cdist(
    g: jit_utils.GraphContext,
    x1,
    x2,
    p=2.0,
    compute_mode="use_mm_for_euclid_dist_if_necessary",
):
    # X1.shape = (B * P * D), X2.shape = (B * R * D)
    # In order to respect numpy style broadcasting as demonstrated in
    # https://github.com/onnx/onnx/blob/main/docs/Broadcasting.md
    # we unsqueeze both input tensors
    row_size_x1 = symbolic_helper._get_tensor_dim_size(x1, -2)
    row_size_x2 = symbolic_helper._get_tensor_dim_size(x2, -2)
    p_float = symbolic_helper._parse_arg(p, "f")
    compute_mode = symbolic_helper._parse_arg(compute_mode, "i")
    if p_float == 2.0 and (
        compute_mode == 1
        or (
            compute_mode is None
            and (
                row_size_x1 is None
                or row_size_x2 is None
                or (row_size_x1 >= 25 and row_size_x2 >= 25)
            )
        )
    ):
        return _euclidean_dist(g, x1, x2)
    rank = symbolic_helper._get_tensor_rank(x1)
    if rank is None:
        raise AssertionError("rank must be non-None")
    broadcasted_x1 = symbolic_helper._unsqueeze_helper(g, x1, [rank - 1])
    broadcasted_x2 = symbolic_helper._unsqueeze_helper(g, x2, [rank - 2])
    return pairwise_distance(
        g, broadcasted_x1, broadcasted_x2, p, eps=1e-06, keepdim=False
    )