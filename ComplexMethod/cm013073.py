def wrapper(g, *args, **kwargs):
            nonlocal scale
            nonlocal zero_point
            if scale is not None:
                _scale = g.op("Constant", value_t=torch.tensor(scale))
            else:
                _scale = None
            if zero_point is not None:
                _zero_point = g.op("Constant", value_t=torch.tensor(zero_point))
            else:
                _zero_point = None

            # Support variable length arguments by marking unspecified ones as non-quantized
            arg_q_descriptors_extended = arg_q_descriptors + (False,) * (
                len(args) - len(arg_q_descriptors)
            )
            descriptor_args = tuple(zip(arg_q_descriptors_extended, args))

            def _is_arg_quantized(descriptor, arg):
                return descriptor and _is_value(arg) and _is_tuple_construct(arg)

            # Run regular symbolic function if none of the argument is QTensor.
            is_quantized: list[bool] = []
            for descriptor, arg in descriptor_args:
                # ListConstruct
                if _is_packed_list(arg):
                    is_quantized.extend(
                        _is_arg_quantized(descriptor, arg_input)
                        for arg_input in arg.node().inputs()
                    )
                else:
                    is_quantized.append(_is_arg_quantized(descriptor, arg))

            if not any(is_quantized):
                return fn(g, *args, **kwargs)

            # Dequantize arguments that are quantized
            non_quantized_args = []
            for descriptor, arg in descriptor_args:
                if _is_arg_quantized(descriptor, arg):
                    # Quantized arg is a tuple of (value, scale, zero_point)
                    dequantized_arg, arg_scale, arg_zero_point, _ = dequantize_helper(
                        g, arg
                    )
                    non_quantized_args.append(dequantized_arg)
                    # Set scale and zero_point to the first quantized input if not already set
                    if _scale is None:
                        _scale = arg_scale
                    if _zero_point is None:
                        _zero_point = arg_zero_point
                # ListConstruct
                elif _is_packed_list(arg):
                    for arg_input in arg.node().inputs():
                        if _is_arg_quantized(descriptor, arg_input):
                            # Quantized arg is a tuple of (value, scale, zero_point)
                            (
                                dequantized_arg,
                                arg_scale,
                                arg_zero_point,
                                _,
                            ) = dequantize_helper(g, arg_input)
                            # Set scale and zero_point to the first quantized input if not already set
                            if _scale is None:
                                _scale = arg_scale
                            if _zero_point is None:
                                _zero_point = arg_zero_point
                            arg_input.replaceAllUsesWith(dequantized_arg)
                    non_quantized_args.append(arg)
                else:
                    # Non-quantized arg
                    non_quantized_args.append(arg)
            # TODO(justinchuby): Only single output is supported for now. We may want to
            # support multiple outputs in the future.
            output = fn(g, *non_quantized_args, **kwargs)

            if _scale is None:
                raise AssertionError("Bug: Scale must be set for quantized operator")
            if _zero_point is None:
                raise AssertionError(
                    "Bug: Zero point must be set for quantized operator"
                )

            if quantize_output:
                return quantize_helper(g, output, _scale, _zero_point)
            return output