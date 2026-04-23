def _construct_node(
    signature: ir.schemas.OpSignature,
    named_inputs: Mapping[str, ir.Value | None],
    named_attrs: Mapping[str, ValidAttributeType],
    opset: onnxscript.values.Opset,
    num_outputs: int,
) -> ir.Node:
    """Construct the node with the inputs and attributes.

    Variadic inputs are flattened.

    Args:
        signature: The OpSignature for the node.
        named_inputs: The mapping of parameter names to their arguments. When we
            do not have the schema of an operator, we do not know the names of
            the inputs, in which case the names can be anything because they
            are not used in this function. The data structure is passed in for
            consistency with the other functions.
        named_attrs: The mapping of attribute names to their values.
        num_outputs: The number of outputs for the node.
    """
    inputs: list[ir.Value | None] = []
    # Flatten variadic inputs
    for value in named_inputs.values():
        if isinstance(value, Sequence):
            inputs.extend(value)
        else:
            inputs.append(value)

    # If final inputs are None, strip them from the node inputs
    for input in reversed(inputs):
        if input is not None:
            break
        inputs.pop()

    # Construct and filter out None attributes
    attributes = [
        attr
        for attr in ir.convenience.convert_attributes(named_attrs)
        if attr.value is not None
    ]
    outputs = [_tensors.SymbolicTensor(opset) for _ in range(num_outputs)]
    return ir.Node(
        signature.domain,
        signature.name,
        inputs=inputs,
        attributes=attributes,
        outputs=outputs,
        version=signature.since_version,
    )