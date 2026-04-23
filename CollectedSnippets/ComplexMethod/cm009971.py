def __torch_function__(
        cls,
        func: Callable,
        types: tuple,
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        if DOT_OPTIMIZED and func is torch.Tensor.__mul__:
            # Check conditions: 2 args, both are tensor-like, both 0-dimensional
            if (
                len(args) == 2
                and not kwargs
                and isinstance(args[0], (_Tensor, torch.Tensor))
                and isinstance(args[1], (_Tensor, torch.Tensor))
            ):
                # Get tensor info for both operands
                lhs_info = TensorInfo.create(
                    args[0], ensure_batched=False, ensure_present=False
                )
                rhs_info = TensorInfo.create(
                    args[1], ensure_batched=False, ensure_present=False
                )

                if (
                    lhs_info
                    and rhs_info
                    and lhs_info.tensor is not None
                    and rhs_info.tensor is not None
                    and lhs_info.tensor.dim() == 0
                    and rhs_info.tensor.dim() == 0
                ):
                    if (
                        lhs_info.tensor.is_floating_point()
                        and rhs_info.tensor.is_floating_point()
                    ):
                        # Collect all unique levels and has_device
                        has_device = lhs_info.has_device or rhs_info.has_device
                        levels = []

                        for level in lhs_info.levels:
                            if level not in levels:
                                levels.append(level)
                        for level in rhs_info.levels:
                            if level not in levels:
                                levels.append(level)

                        # Debug print
                        # print(f"DEBUG: Creating delayed mul, levels: {levels}, has_device: {has_device}")

                        # Create delayed tensor
                        return Tensor.create_delayed(func, args, levels, has_device)

        if func is torch.Tensor.__getitem__:
            from functorch.dim._getsetitem import getitem

            return getitem(cls, func, types, args, kwargs)

        if func is torch.Tensor.__setitem__:
            from functorch.dim._getsetitem import setitem

            # args should be (tensor, index, value)
            if len(args) == 3:
                setitem(args[0], args[1], args[2])
                return None
            else:
                raise ValueError(f"Expected 3 args for __setitem__, got {len(args)}")

        # Fast-path for len; mostly to avoid infinite loop in TestMinFunctorchOnly.test_softmax_split
        if func is torch.Tensor.__len__:
            return args[0].size(0)

        # Special handling for torch.softmax - use the pre-wrapped version
        if func is torch.softmax:
            return softmax(*args, **kwargs)

        # Special handling for torch.stack - use the custom stack function
        if func is torch.stack:
            return stack(*args, **kwargs)

        if (
            func is torch.Tensor.split
            or func is torch._VF.split  # type: ignore[attr-defined]
            or func is torch._VF.split_with_sizes  # type: ignore[attr-defined]
            or func is torch.split
        ):
            return split(*args, **kwargs)

        return _Tensor._torch_function_fallback(func, types, args, kwargs)