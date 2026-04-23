def pad(x, pad_width, mode="constant", constant_values=None):
    kwargs = {}
    if constant_values is not None:
        if mode != "constant":
            raise ValueError(
                "Argument `constant_values` can only be "
                "provided when `mode == 'constant'`. "
                f"Received: mode={mode}"
            )
        kwargs["value"] = constant_values
    x = convert_to_tensor(x)
    pad_sum = []
    pad_width = list(pad_width)[::-1]  # torch uses reverse order
    pad_width_sum = 0
    for pad in pad_width:
        pad_width_sum += pad[0] + pad[1]
    for pad in pad_width:
        pad_sum += pad
        pad_width_sum -= pad[0] + pad[1]
        if pad_width_sum == 0:  # early break when no padding in higher order
            break
    if mode == "symmetric":
        mode = "replicate"
    if mode == "constant":
        return torch.nn.functional.pad(x, pad=pad_sum, mode=mode, **kwargs)
    # TODO: reflect and symmetric padding are implemented for padding the
    # last 3 dimensions of a 4D or 5D input tensor, the last 2 dimensions of a
    # 3D or 4D input tensor, or the last dimension of a 2D or 3D input tensor.
    # https://pytorch.org/docs/stable/generated/torch.nn.functional.pad.html
    ori_dtype = x.dtype
    ori_ndim = x.ndim
    need_squeeze = False
    if x.ndim < 3:
        need_squeeze = True
        new_dims = [1] * (3 - x.ndim)
        x = x.view(*new_dims, *x.shape)
    need_cast = False
    if x.dtype not in (torch.float32, torch.float64):
        # TODO: reflect and symmetric padding are only supported with float32/64
        # https://github.com/pytorch/pytorch/issues/40763
        need_cast = True
        x = cast(x, torch.float32)
    x = torch.nn.functional.pad(x, pad=pad_sum, mode=mode)
    if need_cast:
        x = cast(x, ori_dtype)
    if need_squeeze:
        x = torch.squeeze(x, dim=tuple(range(3 - ori_ndim)))
    return x