def _process_python_sequences(
    signature: ir.schemas.OpSignature,
    named_inputs: dict[str, AllowedArgType],
    type_binding: Mapping[ir.schemas.TypeConstraintParam, ir.TypeProtocol],
    constant_farm: dict[
        tuple[
            bool
            | int
            | float
            | str
            | ir.TensorProtocol
            | tuple[bool, ...]
            | tuple[int, ...]
            | tuple[float, ...],
            ir.DataType,
        ],
        ir.Value,
    ],
    opset: onnxscript.values.Opset,
):
    """Handle three types of sequences.

    1. Variadic inputs
    2. Sequence input of ir.Value,
    3. Sequence of Python constants that contains ir.Value
    """
    for name, arg in named_inputs.items():
        param = signature.params_map[name]
        if not isinstance(param, ir.schemas.Parameter):
            raise AssertionError(f"Expected Parameter, got {type(param)}")

        if not isinstance(arg, (tuple, list)):
            continue

        if len(arg) == 0:
            # Skip empty sequences
            continue

        # 1. Sequence input of ir.Value
        if _allowed_types_are_sequence_types(param.type_constraint.allowed_types):
            # Turn the list into a Sequence node
            # Constant op creation will be handled by the variadic case below when calling
            # the SequenceConstruct op.
            named_inputs[name] = opset.SequenceConstruct(*arg)
            continue

        # 2. Variadic inputs
        # NOTE: Variadic operators like Max can be called with mixed ir.Value and Python constants
        # like `Max(0, ir.Value())`
        # We need to convert the Python constants to Constant nodes
        if param.variadic:
            if all(isinstance(val, ir.Value) for val in arg):
                # Skip the variadic input if all values are ir.Value
                continue

            dtype = _determine_input_dtype(param, arg, type_binding)
            new_args = []
            for val in arg:
                if isinstance(val, ir.Value):
                    new_args.append(val)
                else:
                    constant_tensor = ir.tensor(value=val, dtype=dtype)  # type: ignore[arg-type]
                    constant_value = opset.Constant(value=constant_tensor)
                    new_args.append(constant_value)
            named_inputs[name] = new_args
            continue
        else:
            # 3. Concat the list as a single input
            # E.g. [Value, 42] should be converted to op.Concat(Value, Constant(42))
            # when the expected input type is INT64
            # We assume this only happens for 0D cases
            if all(isinstance(val, ir.Value) for val in arg):
                expanded_args = [_reshape_to_1d_tensor(opset, val) for val in arg]
                named_inputs[name] = opset.Concat(*expanded_args, axis=0)
                continue

            dtype = _determine_input_dtype(param, arg, type_binding)
            new_args = []
            for val in arg:
                if isinstance(val, ir.Value):
                    new_args.append(_reshape_to_1d_tensor(opset, val))
                elif val is None:
                    # Skip None values
                    continue
                elif isinstance(val, (ir.Tensor, ir.TensorProtocol)):
                    new_args.append(
                        _reshape_to_1d_tensor(opset, opset.Constant(value=val))
                    )
                else:
                    # Turn the Python constant into 1D tensor for the constant
                    if not isinstance(val, (bool, int, float)):
                        raise AssertionError(f"Expected int or float, got {type(val)}")
                    new_args.append(
                        _get_or_create_constant(constant_farm, [val], dtype, opset)  # type: ignore[arg-type]
                    )
            named_inputs[name] = opset.Concat(*new_args, axis=0)
            continue
    return named_inputs