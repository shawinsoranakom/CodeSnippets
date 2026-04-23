def lookup_jagged(func, *args, **kwargs) -> Callable | None:
    dispatch_func = JAGGED_OPS_TABLE.get(func, None)
    if dispatch_func is not None:
        return dispatch_func

    # Handle pointwise fallbacks
    if torch.Tag.pointwise in func.tags:
        from torch.fx.experimental.symbolic_shapes import is_nested_int

        # No pointwise ops legitimately accept nested int inputs. Without this check,
        # they will be incorrectly interpreted as tensors.
        # See https://github.com/pytorch/pytorch/issues/138496
        for arg in args:
            if is_nested_int(arg):
                raise RuntimeError(
                    f"NestedTensor {func.__name__}: invalid argument {arg}"
                )

        # Assume there aren't additional tensors that aren't the "unary/binary" args
        num_tensor_args = sum(isinstance(x, torch.Tensor) for x in args)
        if num_tensor_args == 1:
            # Build up the check schema string. The first tensor arg is assumed to be
            # an NJT and other args are sent through as-is.
            schema_parts = []
            for arg in func._schema.arguments:
                if isinstance(arg.type, torch.TensorType):
                    schema_parts.append(f"{arg.name}: jt_all")
                    break
                else:
                    schema_parts.append(f"{arg.name}: any")
            schema_parts.append("...")
            check_schema_str = ", ".join(schema_parts)
            check_schema(check_schema_str, func, *args, **kwargs)
            return functools.partial(jagged_unary_pointwise, func)
        elif num_tensor_args == 2:
            check_schema("lhs: any, rhs: any, ...", func, *args, **kwargs)
            return functools.partial(jagged_binary_pointwise, func)

    return None