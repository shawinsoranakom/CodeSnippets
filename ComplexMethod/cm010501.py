def conv(
    fake_mode: FakeTensorMode, func: OpOverload, *args: Any, **kwargs: Any
) -> FakeTensor | tuple[FakeTensor | None, FakeTensor | None, FakeTensor | None]:
    _, new_kwargs = _normalize_function_or_error(
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )
    input_ = new_kwargs["input"]
    weight = new_kwargs["weight"]
    device = input_.fake_device
    # need to re-enable mode so the tensors report fake device
    with fake_mode:
        # if the input is unsqueezed in Convolution.cpp we get segfault
        k = weight.ndim

        # Avoid importing sympy at a module level
        from torch.fx.experimental.symbolic_shapes import has_guarding_hint

        all_hinted = all(has_guarding_hint(s) for s in input_.shape) and all(
            has_guarding_hint(s) for s in weight.shape
        )

        if not all_hinted:
            # TODO: We can make this a little more faithful with best effort
            # channels last detection (but only if it's statically obvious!)
            mem_fmt = None
        else:
            # convolution has "bias" but not "bias_sizes"; convolution_backward
            # has "bias_sizes" but not "bias". .get() handles both with one call.
            bias = new_kwargs.get("bias")
            select_kwargs: dict[str, object] = dict(
                stride=new_kwargs["stride"],
                padding=new_kwargs["padding"],
                dilation=new_kwargs["dilation"],
                transposed=new_kwargs["transposed"],
                output_padding=new_kwargs["output_padding"],
                groups=new_kwargs["groups"],
                bias=bias,
            )
            if bias is None:
                select_kwargs["bias_sizes"] = new_kwargs.get("bias_sizes")
            conv_backend = torch._C._select_conv_backend(
                input_, weight, **select_kwargs
            )
            # Expand 1d -> 2d.
            # Note: Avoid expanding before calling _select_conv_backend,
            # as the function handles 2D expansion internally.
            if k == 3 and not input_.is_mkldnn and not input_.is_xpu:
                # Note: Using input.to(memory_format=contiguous) does not work.
                input_ = input_.contiguous().unsqueeze(2)
                weight = weight.unsqueeze(2)
            mem_fmt = torch._C._conv_determine_backend_memory_format(
                input_, weight, conv_backend
            )

    def convert(
        t: torch.Tensor | None, mem_fmt: torch.memory_format | None
    ) -> FakeTensor | None:
        if t is None:
            return t
        if mem_fmt is not None:
            # channels last only support 4d, try to expand dim then convert it back later.
            if t.dim() == 3 and mem_fmt == torch.channels_last:
                t = t.unsqueeze(2).to(memory_format=mem_fmt).squeeze(2)
            else:
                t = t.to(memory_format=mem_fmt)
        return FakeTensor(fake_mode, t, device)

    with in_kernel_invocation_manager(fake_mode):
        out = func(**new_kwargs)

        if func is aten.convolution.default:
            return convert(out, mem_fmt)  # type: ignore[return]
        else:
            return (
                convert(out[0], mem_fmt),
                convert(out[1], mem_fmt),
                convert(out[2], None),
            )