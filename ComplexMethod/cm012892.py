def _maybe_recursive_remove_dequantize(arg: Any, node: Node, graph: Graph) -> None:
    """If the arg is a dequantize Node, or a list/tuple/dict of dequantize Node,
    we'll recursively remove the dequantize Node
    """
    if isinstance(arg, Node) and arg.op == "call_method" and arg.target == "dequantize":
        quantize_node = arg.args[0]
        # we only replace the specific use since dequantize could be used by other nodes
        # as well
        node.replace_input_with(arg, quantize_node)
    elif isinstance(arg, (list, tuple)):
        for arg_element in arg:
            _maybe_recursive_remove_dequantize(arg_element, node, graph)
    elif isinstance(arg, dict):
        for arg_element in arg.values():
            _maybe_recursive_remove_dequantize(arg_element, node, graph)
    else:
        warnings.warn(
            f"Unsupported node type in recursive remove dequantize: {type(arg)}",
            stacklevel=2,
        )