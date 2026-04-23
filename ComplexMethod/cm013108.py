def _handle_call_function_node(
    graph_like: ir.Graph | ir.Function,
    node: torch.fx.Node,
    node_name_to_values: dict[str, ir.Value | Sequence[ir.Value]],
) -> None:
    """Handle a call_function node.

    Args:
        graph: The ONNX graph at construction.
        node: The FX node to translate.
        node_name_to_values: A mapping of FX node names to their produced ir.Value.
    """
    if node.target is operator.getitem:
        _handle_getitem_node(node, node_name_to_values)
    # Add op to the graph
    op = str(node.target)
    fx_inputs, attributes, input_names, output_names = _get_inputs_and_attributes(node)
    inputs: list[ir.Value | None] = []
    for i, input_ in enumerate(fx_inputs):
        if input_ is None:
            inputs.append(None)
        elif hasattr(input_, "name"):
            if isinstance(input_, torch.fx.Node) and input_.target is operator.getitem:
                actual_input = _handle_getitem_node(input_, node_name_to_values)
                inputs.append(actual_input)
            else:
                value = node_name_to_values[input_.name]
                if isinstance(value, Sequence):
                    raise AssertionError(f"Unexpected sequence value for {input_.name}")
                inputs.append(value)
        else:
            attributes[f"arg_{i}"] = input_

    outputs = [ir.Value(name=name) for name in output_names]
    if len(outputs) > 1:
        _set_shape_types(outputs, node.meta["val"], complex_to_float=False)
        node_name_to_values[node.name] = outputs
    else:
        _set_shape_type(outputs[0], node.meta["val"], complex_to_float=False)
        node_name_to_values[node.name] = outputs[0]
    ir_node = ir.Node(
        "pkg.torch.ops",
        op,
        inputs,
        attributes=ir_convenience.convert_attributes(attributes),
        outputs=outputs,
        name=node.name,
    )
    ir_node.meta["node"] = node
    ir_node.metadata_props["pkg.torch.onnx.input_names"] = repr(input_names)
    # Record the nn.Module stack for the node
    _set_node_metadata(node, ir_node)

    graph_like.append(ir_node)