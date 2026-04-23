def meta_max_pool3d_with_indices(
    input,
    kernel_size,
    stride=(),
    padding=(0,),
    dilation=(1,),
    ceil_mode=False,
):
    torch._check(
        len(kernel_size) in (1, 3),
        lambda: "max_pool3d: kernel_size must either be a single int, or a tuple of three ints",
    )
    kT = kernel_size[0]
    kH = kT if len(kernel_size) == 1 else kernel_size[1]
    kW = kT if len(kernel_size) == 1 else kernel_size[2]

    torch._check(
        not stride or len(stride) in (1, 3),
        lambda: "max_pool3d: stride must either be omitted, a single int, or a tuple of three ints",
    )
    dT = kT if not stride else stride[0]
    dH = kH if not stride else (dT if len(stride) == 1 else stride[1])
    dW = kW if not stride else (dT if len(stride) == 1 else stride[2])

    torch._check(
        len(padding) in (1, 3),
        lambda: "max_pool3d: padding must either be a single int, or a tuple of three ints",
    )
    pT = padding[0]
    pH = pT if len(padding) == 1 else padding[1]
    pW = pT if len(padding) == 1 else padding[2]

    torch._check(
        len(dilation) in (1, 3),
        lambda: "max_pool3d: dilation must be either a single int, or a tuple of three ints",
    )
    dilationT = dilation[0]
    dilationH = dilationT if len(dilation) == 1 else dilation[1]
    dilationW = dilationT if len(dilation) == 1 else dilation[2]

    torch._check(
        input.ndim in (4, 5),
        lambda: "non-empty 4D or 5D (batch mode) tensor expected for input",
    )

    nbatch = input.size(-5) if input.ndim == 5 else 1
    nslices = input.size(-4)
    itime = input.size(-3)
    iheight = input.size(-2)
    iwidth = input.size(-1)

    otime = pooling_output_shape(itime, kT, pT, dT, dilationT, ceil_mode)
    oheight = pooling_output_shape(iheight, kH, pH, dH, dilationH, ceil_mode)
    owidth = pooling_output_shape(iwidth, kW, pW, dW, dilationW, ceil_mode)

    pool3d_shape_check(
        input,
        nslices,
        kT,
        kH,
        kW,
        dT,
        dH,
        dW,
        pT,
        pH,
        pW,
        dilationT,
        dilationH,
        dilationW,
        itime,
        iheight,
        iwidth,
        otime,
        oheight,
        owidth,
        "max_pool3d_with_indices()",
    )

    # channels_last_3d only applies to 5D tensors (C++ enforces this)
    channels_last = (
        input.ndim == 5 and utils.suggest_memory_format(input) == torch.channels_last_3d
    )
    if input.ndim == 4:
        out_shape = (nslices, otime, oheight, owidth)
    else:
        out_shape = (nbatch, nslices, otime, oheight, owidth)  # type: ignore[assignment]

    out = input.new_empty(out_shape)
    indices = input.new_empty(out_shape, dtype=torch.int64)

    if channels_last:
        out = out.to(memory_format=torch.channels_last_3d)
        indices = indices.to(memory_format=torch.channels_last_3d)

    return out, indices