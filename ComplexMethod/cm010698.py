def _upsample_linear(
    input: Tensor,
    output_size: list[int],
    align_corners: bool,
    scales: list[float | None],
) -> Tensor:
    # get dimensions of original image
    n_channels = input.shape[1]
    inp_sizes = input.shape[2:]
    n_dims = len(inp_sizes)

    _, dtype = utils.elementwise_dtypes(
        input,
        type_promotion_kind=utils.ELEMENTWISE_TYPE_PROMOTION_KIND.INT_TO_FLOAT,
    )

    def get_values(inp_size, out_size, scales, nsqueeze):
        # First Calculate scaling factor
        scale_factor = _compute_scale(inp_size, out_size, align_corners, scales)
        # We have to create arange with int64 dtype and use .to in order to avoid
        # additional kernels creation in inductor and get a perf slowdown
        i = torch.arange(out_size, device=input.device).to(dtype=dtype)

        x_f32 = _compute_source_index(scale_factor, i, align_corners).clamp(min=0.0)
        x_f32 = x_f32.reshape(x_f32.shape[0], *[1] * (nsqueeze))
        x = x_f32.to(torch.int64)
        xp1 = (x + 1).clamp(max=inp_size - 1)
        return x_f32, x, xp1

    values = [
        get_values(inp_size, out_size, scales, n_dims - 1 - i)
        for i, (inp_size, out_size, scales) in enumerate(
            zip(inp_sizes, output_size, scales)
        )
    ]
    xs_f32, xs, xp1s = list(zip(*values))

    vs = []
    for a in product(*[[0, 1]] * n_dims):
        idx = [None, None] + [xs[k] if a[k] == 0 else xp1s[k] for k in range(n_dims)]
        v = aten._unsafe_index(input, idx)
        v = _maybe_convert_to_dtype(v, dtype)
        vs.append(v)

    for i in reversed(range(n_dims)):
        xscale = (xs_f32[i] - xs[i]).clamp(0.0, 1.0).to(dtype)
        vs = [
            # x1 * (1 - alpha) + x2 * alpha == x1 + (x2 - x1) * alpha
            v1 + torch.mul(v2 - v1, xscale)
            for v1, v2 in zip(vs[::2], vs[1::2])
        ]

    if len(vs) != 1:
        raise AssertionError(f"Expected vs to have exactly 1 element, got {len(vs)}")
    result = vs[0]

    # convert output to correct memory format, if necessary
    memory_format = utils.suggest_memory_format(input)

    # following "heuristic: only use channels_last path when it's faster than the contiguous path"
    if input.device.type == "cuda" and n_channels < 16:
        memory_format = torch.contiguous_format

    if not isinstance(result, torch.Tensor):
        raise AssertionError(
            f"Expected result to be a Tensor, got {type(result).__name__}"
        )

    result = result.contiguous(memory_format=memory_format)

    if not input.is_floating_point():
        result = result.round()

    return result