def upsample_bicubic2d_default(
    input: Tensor,
    output_size: tuple[int, int],
    align_corners: bool,
    scale_h: float | None = None,
    scale_w: float | None = None,
) -> Tensor:
    # get dimensions of original image
    _, _, in_h, in_w = input.shape

    # Calculate horizontal and vertical scaling factor
    h_scale_factor = _compute_scale(in_h, output_size[0], align_corners, scale_h)
    w_scale_factor = _compute_scale(in_w, output_size[1], align_corners, scale_w)

    _, dtype = utils.elementwise_dtypes(
        input, type_promotion_kind=utils.ELEMENTWISE_TYPE_PROMOTION_KIND.INT_TO_FLOAT
    )

    # We have to create arange with int64 dtype and use .to in order to avoid
    # additional kernels creation in inductor and get a perf slowdown
    i = torch.arange(output_size[0], device=input.device).to(dtype=dtype)
    j = torch.arange(output_size[1], device=input.device).to(dtype=dtype)

    x_float = _compute_source_index(w_scale_factor, j, align_corners)
    y_float = _compute_source_index(h_scale_factor, i, align_corners)
    y_float = y_float.unsqueeze(-1)

    x = x_float.floor()
    y = y_float.floor()

    # We should also clamp xscale/yscale
    # See guard_index_and_lambda in UpSample.h
    yscale = (y_float - y).clamp(0.0, 1.0)
    xscale = (x_float - x).clamp(0.0, 1.0)
    x = x.to(torch.int64)
    y = y.to(torch.int64)

    iys_ofs = (y - 1, y, y + 1, y + 2)
    ixs_ofs = (x - 1, x, x + 1, x + 2)

    weights_x = _upsample_get_cubic_coefficients(xscale)
    weights_y = _upsample_get_cubic_coefficients(yscale)

    weights_precision_x, weights_precision_y = None, None
    if input.dtype == torch.uint8:
        weights_precision_x = _compute_weight_precision(weights_x)
        weights_precision_y = _compute_weight_precision(weights_y)

        weights_x = [
            (w * (1 << weights_precision_x) + torch.sign(w) * 0.5).to(torch.int16)
            for w in weights_x
        ]
        weights_y = [
            (w * (1 << weights_precision_y) + torch.sign(w) * 0.5).to(torch.int16)
            for w in weights_y
        ]

    def load_bounded(ys, xs):
        y_idx = torch.clamp(ys, 0, in_h - 1)
        x_idx = torch.clamp(xs, 0, in_w - 1)
        v = aten._unsafe_index(input, [None, None, y_idx, x_idx])
        return v

    def get_x_interp(y):
        src_x = tuple(load_bounded(y, x_ofs) for x_ofs in ixs_ofs)
        if input.dtype == torch.uint8:
            if weights_precision_x is None:
                raise AssertionError(
                    "weights_precision_x must not be None for uint8 input"
                )
            return _sum_tensors_uint8(src_x, weights_x, weights_precision_x)
        return _sum_tensors(c1 * c2 for (c1, c2) in zip(src_x, weights_x))

    src_y = tuple(get_x_interp(y_ofs) for y_ofs in iys_ofs)
    if input.dtype == torch.uint8:
        if weights_precision_y is None:
            raise AssertionError("weights_precision_y must not be None for uint8 input")
        result = _sum_tensors_uint8(src_y, weights_y, weights_precision_y)
    else:
        result = _sum_tensors(c1 * c2 for (c1, c2) in zip(src_y, weights_y))

    # convert output to correct memory format, if necessary
    memory_format = utils.suggest_memory_format(input)
    result = result.contiguous(memory_format=memory_format)
    return result