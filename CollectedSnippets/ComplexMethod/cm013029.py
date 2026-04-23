def _create_node(
    graph_or_block: _C.Graph | _C.Block,
    domain_op: str,
    inputs: Sequence,
    attributes: dict,
    params_dict: dict,
    opset_version: int,
    n_outputs: int,
    shape_inference: bool = True,
) -> _C.Node:
    """Creates an node 'domain_op', taking inputs and attributes."""
    if isinstance(graph_or_block, _C.Graph):
        graph = graph_or_block
        node = graph.create(domain_op, inputs, n_outputs)
        node = graph.insertNode(node)
    elif isinstance(graph_or_block, _C.Block):
        block = graph_or_block
        node = block.addNode(domain_op, inputs)

        # Block does not have create defined, so we need to add outputs manually
        if n_outputs > 1:
            for _ in range(1, n_outputs):
                node.addOutput()

    node_outputs = tuple(node.outputs())  # type: ignore[possibly-undefined]
    if len(node_outputs) != n_outputs:
        raise AssertionError(
            f"len(node_outputs)={len(node_outputs)} != n_outputs={n_outputs}"
        )

    aten = domain_op.startswith("aten::")

    # Add all attributes
    for key, value in sorted(attributes.items()):
        if key in _SKIP_NODE_ATTRIBUTES:
            continue
        # pyrefly: ignore [unbound-name]
        _add_attribute(node, key, value, aten=aten)
    if shape_inference:
        # pyrefly: ignore [unbound-name]
        _C._jit_pass_onnx_node_shape_type_inference(node, params_dict, opset_version)
    # pyrefly: ignore [unbound-name]
    return node