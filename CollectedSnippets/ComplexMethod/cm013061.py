def _parse_arg(
    value,
    desc: _ValueDescriptor,
    arg_name: str | None = None,
    node_name: str | None = None,
):
    if desc == "none":
        return value
    if desc == "v" or not _is_value(value):
        return value

    node = value.node()
    if node.mustBeNone():
        return None
    if node.kind() == "onnx::Constant":
        node_val = _node_get(node, "value")
        if desc == "i":
            return int(node_val)
        elif desc == "f":
            return float(node_val)
        elif desc == "b":
            return bool(node_val)
        elif desc == "s":
            return str(node_val)
        elif desc == "t":
            return node_val
        elif desc == "is":
            return [int(v) for v in node_val]
        elif desc == "fs":
            return [float(v) for v in node_val]
        else:
            raise errors.SymbolicValueError(
                f"ONNX symbolic does not understand the Constant node '{node}' "
                f"specified with descriptor '{desc}'.",
                value,
            )
    elif node.kind() == "prim::ListConstruct":
        if desc == "is":
            for v in node.inputs():
                element_node = v.node()
                if element_node.kind() != "onnx::Constant":
                    raise errors.SymbolicValueError(
                        f"Failed to export a node '{element_node}' "
                        f"(in list node {node}) "
                        f"because it is not constant. "
                        f"Please try to make things (e.g. kernel sizes) static if possible.",
                        value,
                    )
            return [int(_node_get(v.node(), "value")) for v in value.node().inputs()]
        else:
            raise errors.SymbolicValueError(
                f"ONNX symbolic does not know how to unpack the ListConstruct node that "
                f"is not a list of integers: '{node}'",
                value,
            )

    if arg_name is None or node_name is None:
        raise errors.SymbolicValueError(
            f"Expected node type 'onnx::Constant', got '{node.kind()}'.",
            value,
        )

    raise errors.SymbolicValueError(
        "Expected node type 'onnx::Constant' "
        f"for argument '{arg_name}' of node '{node_name}', got '{node.kind()}'.",
        value,
    )