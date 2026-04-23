def _torch_function_fallback(
        func: Callable, types: tuple, args: tuple, kwargs: dict
    ) -> Any:
        """Fallback torch function implementation for non-special-cased functions."""
        is_pointwise = POINTWISE_OPTIMIZE and func in op_properties.pointwise
        # TODO: optimize pytree here
        flat_args, spec = tree_flatten((args, kwargs))
        device_holding_tensor = None

        infos: list[TensorInfo] = []
        result_levels: list[DimEntry] = []

        for f in flat_args:
            info = TensorInfo.create(f, not is_pointwise, False)
            infos.append(info)
            if info:
                if not (is_pointwise or info.batchedtensor is not None):
                    raise AssertionError(
                        "Expected pointwise or batchedtensor to be set"
                    )
                if device_holding_tensor is None and info.has_device:
                    device_holding_tensor = info.tensor
                # Collect all unique levels
                for level in info.levels:
                    if not isinstance(level, DimEntry):
                        raise AssertionError(f"Expected DimEntry, got {type(level)}")
                    if level not in result_levels:
                        result_levels.append(level)

        if is_pointwise:
            # Pointwise operation: match all tensors to common levels
            for i, info in enumerate(infos):
                if info and info.tensor is not None:
                    tensor = info.tensor
                    if device_holding_tensor is not None and not info.has_device:
                        tensor = tensor.to(device_holding_tensor.device)
                    ml = _match_levels(tensor, info.levels, result_levels)
                    flat_args[i] = handle_from_tensor(ml)

            unflat_args, unflat_kwargs = tree_unflatten(flat_args, spec)
            result = func(*unflat_args, **unflat_kwargs)

            # Wrap tensor results
            def wrap_tensor(obj: Any) -> Any:
                if isinstance(obj, torch.Tensor):
                    return Tensor.from_positional(
                        obj, result_levels, device_holding_tensor is not None
                    )
                return obj

            # Small fastpath
            if isinstance(result, torch.Tensor):
                return wrap_tensor(result)
            else:
                return tree_map(wrap_tensor, result)

        # Non-pointwise operation: use functorch vmap layers
        with EnableAllLayers(result_levels) as guard:
            # Update arguments with batched tensors
            for i, info in enumerate(infos):
                if info and info.batchedtensor is not None:
                    batched = info.batchedtensor
                    if device_holding_tensor is not None and not info.has_device:
                        batched = batched.to(device_holding_tensor.device)
                    guard.inplace_update_layers(batched, info.levels)
                    flat_args[i] = handle_from_tensor(batched)

            unflat_args, unflat_kwargs = tree_unflatten(flat_args, spec)
            result = func(*unflat_args, **unflat_kwargs)

            # Unwrap results from functorch layers
            def unwrap_tensor(obj: Any) -> Any:
                if isinstance(obj, torch.Tensor):
                    return guard.from_batched(obj, device_holding_tensor is not None)
                return obj

            if isinstance(result, torch.Tensor):
                return unwrap_tensor(result)
            else:
                return tree_map(unwrap_tensor, result)