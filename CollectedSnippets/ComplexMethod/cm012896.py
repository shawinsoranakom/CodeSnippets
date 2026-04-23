def convert_custom_module(
    node: Node,
    graph: Graph,
    modules: dict[str, torch.nn.Module],
    custom_module_class_mapping: dict[QuantType, dict[type, type]],
    statically_quantized_custom_module_nodes: set[Node],
) -> None:
    """Converts an observed custom module to a quantized custom module based on
    `custom_module_class_mapping`
    For static quantization, we'll also remove the previous `dequantize` node and
    attach the observer node for output to the module, the observer for the node
    will be converted to a dequantize node instead of quantize-dequantize pairs
    later in the graph. In the end we would have a quantized custom module that
    has the same interface as a default quantized module in nn.quantized namespace,
    i.e. quantized input and quantized output.

    Args:
      - node: The call_module node of the observed standalone module
      - graph: The graph containing the node
      - modules: named_module of original model
      - custom_module_class_mapping: mapping from observed custom module class to
        quantized custom module class, used to swap custom modules
      - statically_quantized_custom_module_nodes: we'll add the custom module node
        if we find it is statically quantized, this will be used later when converting
        observers to quant/dequant node pairs, if the observed node is a statically
        quantized custom module nodes, we'll convert the observer to a dequantize node,
        this is to keep the interface the same as the default quantized module.
        TODO: maybe we want to redesign this part to align with reference model design
        as well, but there has been some discussions around the interface, so we can do
        it later.
    """
    observed_custom_module = modules[str(node.target)]
    qconfig = observed_custom_module.qconfig
    if activation_is_statically_quantized(qconfig):
        statically_quantized_custom_module_nodes.add(node)
        if _is_custom_module_lstm(node, modules):
            # The inputs are tuples in the form (input, (hidden0, hidden1))
            # Ensure all three input nodes are quantized
            if not (
                len(node.args) == 2
                and isinstance(node.args[1], tuple)
                and len(node.args[1]) == 2
            ):
                raise AssertionError(
                    "Expected LSTM custom module inputs to be (input, (hidden0, hidden1))"
                )
            (inputs, (hidden0, hidden1)) = node.args  # type: ignore[misc]
            if not isinstance(inputs, Node):
                raise AssertionError("Expected inputs to be a Node")
            if not isinstance(hidden0, Node):
                raise AssertionError("Expected hidden0 to be a Node")
            if not isinstance(hidden1, Node):
                raise AssertionError("Expected hidden1 to be a Node")
            _remove_previous_dequantize_in_custom_module(node, inputs, graph)
            _remove_previous_dequantize_in_custom_module(node, hidden0, graph)
            _remove_previous_dequantize_in_custom_module(node, hidden1, graph)
        elif _is_custom_module_mha(node, modules):
            # Inputs are in the form (query, key, value)
            # TODO: This is the first step in enabling the full fx custom module
            # quantization path for MultiheadAttention, and only covers the inputs
            # to the module.
            # Additional handling is yet to be implemented for the outputs, similar
            # to LSTM custom module
            if len(node.args) != 3:
                raise AssertionError(
                    "Expected MHA custom module inputs to be (query, key, value)"
                )
            query, key, value = node.args
            if not isinstance(query, Node):
                raise AssertionError("Expected query to be a Node")
            if not isinstance(key, Node):
                raise AssertionError("Expected key to be a Node")
            if not isinstance(value, Node):
                raise AssertionError("Expected value to be a Node")
            _remove_previous_dequantize_in_custom_module(node, query, graph)
            _remove_previous_dequantize_in_custom_module(node, key, graph)
            _remove_previous_dequantize_in_custom_module(node, value, graph)
        else:
            # remove the previous dequant node to ensure the inputs are quantized
            arg = node.args[0]
            if not isinstance(arg, Node):
                raise AssertionError("Expected arg to be a Node")
            _remove_previous_dequantize_in_custom_module(node, arg, graph)
            # absorb the following observer into the module conversion
            activation_post_process = _maybe_get_observer_for_node(node, modules)
            if activation_post_process is None:
                raise AssertionError(
                    "Expected activation_post_process to be present for observed custom module"
                )
            observed_custom_module.activation_post_process = activation_post_process

    # swap the observed custom module to quantized custom module
    quantized_custom_module_class = get_swapped_custom_module_class(
        observed_custom_module, custom_module_class_mapping, qconfig
    )
    quantized_custom_module = quantized_custom_module_class.from_observed(
        observed_custom_module
    )
    parent_name, name = _parent_name(node.target)
    setattr(modules[parent_name], name, quantized_custom_module)