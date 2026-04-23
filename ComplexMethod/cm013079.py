def _process_python_constants(
    signature: ir.schemas.OpSignature,
    named_inputs: dict[str, AllowedArgType],
    type_binding: Mapping[ir.schemas.TypeConstraintParam, ir.TypeProtocol],
    constant_farm: dict[
        tuple[
            bool | int | float | str | tuple[int, ...] | tuple[float, ...],
            ir.DataType,
        ],
        ir.Value,
    ],
    opset: onnxscript.values.Opset,
) -> dict[str, ir.Value | None]:
    """Convert Python constants to Constant nodes and list to Sequence nodes based on the dtype information.

    The added constants will be replacing values in named_inputs in place.

    Args:
        signature: The OpSignature for the node.
        named_inputs: The mapping of parameter names to their arguments.
        type_binding: A mapping of Constraint names to ir.DataType.
        constant_farm: A dictionary of {(py_value, ir.DataType): ir.Value} to store the deduplicated constants.
        opset: The Opset to use for creating Constant nodes.

    Returns:
        A mapping of parameter names to Python constants converted to constant Nodes.
    """
    # 3. Convert Python constants to Constant nodes based on the dtype information;
    #    construct sequences
    #   a. Iterate over all parameters in the signature the second time
    #   b. If the parameter is in to_resolve_type:
    #       - If param.constraint in type_binding,
    #         Get the constant from constant_farm (deduplicated);
    #            otherwise set named_inputs[param.name] = Constant(value, dtype=type_binding[param.constraint])
    #       - Otherwise, set named_inputs[param.name] = Constant(value)
    for name, arg in named_inputs.items():
        param = signature.params_map[name]
        if not isinstance(param, ir.schemas.Parameter):
            raise AssertionError(f"Expected Parameter, got {type(param)}")

        if isinstance(arg, ir.Value):
            # TODO(justinchuby): Cast the ir.Value here if needed
            continue

        if (
            isinstance(arg, Sequence)
            and len(arg) > 0
            and any(isinstance(val, ir.Value) for val in arg)
        ):
            # Skip the sequence of ir.Value. This is a variadic input or a Sequence input
            # It will be handled by _process_python_sequences
            continue
        if param.variadic:
            # Handled by _process_python_sequences
            continue
        if _allowed_types_are_sequence_types(param.type_constraint.allowed_types):
            # Handled by _process_python_sequences
            continue

        dtype = _determine_input_dtype(param, arg, type_binding)

        if arg is None:
            constant_value = None
        elif isinstance(arg, (ir.Tensor, ir.TensorProtocol)):
            constant_value = opset.Constant(value=arg)
        else:
            # Deduplicate the constants
            constant_value = _get_or_create_constant(constant_farm, arg, dtype, opset)  # type: ignore[arg-type]

        named_inputs[param.name] = constant_value
    return named_inputs