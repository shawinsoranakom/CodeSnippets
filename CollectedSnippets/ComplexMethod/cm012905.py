def _match_static_pattern(
    node: Node,
    modules: dict[str, nn.Module],
    qconfig_map: dict[str, QConfigAny],
    matching_modules_or_ops: list[Callable],
    dequantize_node_arg_indices: list[int],
) -> tuple[Node, Node, Node] | tuple[None, None, None]:
    """
    Match the pattern (dequantize - ref node - quantize) against the node provided.

    If there is a match, return a 3-tuple of:
      1) q_node: the quantize node,
      2) relu_node: a relu node wrapping the ref_node, and
      3) ref_node: a reference module or functional node to replace with its quantized counterpart
    Otherwise, if there is no match, return a 3-tuple of (None, None, None).

    Parameters:
      node: The `torch.fx.Node` to match against.
      modules: A mapping from node names to modules in the model graph, used for module lookup.
      qconfig_map: A mapping from node names to the qconfigs associated with the nodes.
          If the corresponding qconfig for the reference node is None, then return no match.
      matching_modules_or_ops: Either a list of functions or a list of `torch.nn.Module`s.
          If the reference node is not in this list, then return no match.
      dequantize_node_arg_indices: A list of indices in the reference node args where dequantize
          nodes may be present. An empty list means skipping the check for dequantize nodes.
    """
    SKIP_LOWERING_VALUE = (None, None, None)

    # Match quantize node
    if node.op != "call_function" or node.target != torch.quantize_per_tensor:
        return SKIP_LOWERING_VALUE
    q_node = node
    ref_node = q_node.args[0]
    if not isinstance(ref_node, Node):
        raise AssertionError("Expected the reference node to be a torch.fx Node")

    # Handle cases where the node is wrapped in a ReLU
    if (ref_node.op == "call_function" and ref_node.target in (F.relu, torch.relu)) or (
        ref_node.op == "call_module" and type(_get_module(ref_node, modules)) is nn.ReLU
    ):
        relu_node = ref_node
        ref_node = relu_node.args[0]
        if not isinstance(ref_node, Node):
            raise AssertionError(
                "Expected the reference node after ReLU to be a torch.fx Node"
            )
    else:
        relu_node = None
    if should_skip_lowering(ref_node, qconfig_map):
        return SKIP_LOWERING_VALUE

    # Match reference module or functional
    if isinstance(matching_modules_or_ops[0], type) and issubclass(
        matching_modules_or_ops[0], nn.Module
    ):
        expected_op = "call_module"
        match_key = type(_get_module(ref_node, modules))
    else:
        expected_op = "call_function"
        match_key = ref_node.target  # type: ignore[assignment]
    if ref_node.op != expected_op or match_key not in matching_modules_or_ops:
        return SKIP_LOWERING_VALUE

    # Match dequantize node(s). Both of the following conditions must pass:
    # (1) All `torch.fx.Node`s at the matching indices must be a dequantize node
    # (2) There must be at least one dequantize node
    matched_dequantize = False
    for i in dequantize_node_arg_indices:
        if i >= len(ref_node.args):
            raise AssertionError(
                f"Dequantize index {i} exceeded reference node's arg length {len(ref_node.args)}"
            )
        arg = ref_node.args[i]
        if is_dequantize_node(arg):
            matched_dequantize = True
        elif isinstance(arg, Node):
            return SKIP_LOWERING_VALUE
    if not matched_dequantize:
        return SKIP_LOWERING_VALUE

    return (q_node, relu_node, ref_node)