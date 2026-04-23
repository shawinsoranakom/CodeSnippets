def jagged_torch_function(func, *args, **kwargs):
    # SDPA has special kernels that handle nested tensors.
    # Dispatch to the correct implementation here
    if func is torch._C._nn.scaled_dot_product_attention:
        return jagged_scaled_dot_product_attention(*args, **kwargs)

    if func.__name__ == "apply_":
        func(args[0]._values, *args[1:], **kwargs)
        return args[0]

    # Handle flatten() here because it's CompositeImplicit.
    if func.__name__ == "flatten":

        def _flatten_sig(input, start_dim=0, end_dim=-1) -> None:
            pass

        _, new_kwargs = normalize_function(  # type: ignore[misc]
            _flatten_sig, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
        )

        inp = new_kwargs.pop("input")

        # NB: stay in outer dim space because we're going to redispatch on a NT input
        start_dim = _wrap_jagged_dim(
            inp.dim(),
            new_kwargs["start_dim"],
            inp._ragged_idx,
            "flatten",
            convert_to_inner_dim=False,
        )
        end_dim = _wrap_jagged_dim(
            inp.dim(),
            new_kwargs["end_dim"],
            inp._ragged_idx,
            "flatten",
            convert_to_inner_dim=False,
        )

        if start_dim == end_dim:
            return inp

        product = functools.reduce(operator.mul, inp.shape[start_dim : end_dim + 1])
        new_shape = (*inp.shape[:start_dim], product, *inp.shape[end_dim + 1 :])

        return inp.reshape(*new_shape)

    # Handle NestedTensor share_memory_.
    if func.__name__ == "share_memory_":
        nt = args[0]

        if nt.is_cuda:
            return nt

        names, _ = nt.__tensor_flatten__()
        with torch._C.DisableTorchFunctionSubclass():
            for name in names:
                component = getattr(nt, name, None)
                if component is not None:
                    component.share_memory_()
        return nt

    # Handle NestedTensor is_shared.
    if func.__name__ == "is_shared":
        nt = args[0]

        if nt.is_cuda:
            return False

        names, _ = nt.__tensor_flatten__()
        if not names:
            return False
        return all(
            getattr(nt, name) is not None and getattr(nt, name).is_shared()
            for name in names
        )

    # Handle nested-specific input validation for CompositeImplicit rms_norm
    if func.__name__ == "rms_norm":

        def _rms_norm_sig(input, normalized_shape, weight=None, eps=None) -> None:
            pass

        _, new_kwargs = normalize_function(  # type: ignore[misc]
            _rms_norm_sig, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
        )

        inp = new_kwargs.pop("input")
        normalized_shape = new_kwargs.pop("normalized_shape")

        # can't normalize over the ragged dim (yet)
        max_normalizable = inp.dim() - inp._ragged_idx - 1
        if len(normalized_shape) > max_normalizable:
            raise ValueError(
                "rms_norm(): Normalization over the ragged dim not supported for nested tensors"
            )

        with torch._C.DisableTorchFunctionSubclass():
            return func(*args, **kwargs)

    raise NotImplementedError(func)