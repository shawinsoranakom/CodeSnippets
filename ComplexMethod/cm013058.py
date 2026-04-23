def prim_constant(g: jit_utils.GraphContext, *inputs, **attrs):
    node = g.original_node

    if node.mustBeNone():
        return None
    # This must go before checking for string values, because some device constants
    # have string values, but we want to keep them as unconverted Device types so
    # that eq() can work on them.
    if isinstance(node.output().type(), _C.DeviceObjType):
        return None
    if node.kindOf("value") == "t":
        return g.op("Constant", value_t=symbolic_helper._node_get(node, "value"))
    if node.kindOf("value") == "s":
        return g.op("Constant", value_s=symbolic_helper._node_get(node, "value"))
    if node.output().type().isSubtypeOf(
        _C.ListType.ofInts()
    ) or node.output().type().isSubtypeOf(_C.ListType.ofFloats()):
        return g.op(
            "Constant", value_t=torch.tensor(symbolic_helper._node_get(node, "value"))
        )
    if node.output().type().isSubtypeOf(_C.ListType.ofStrings()):
        str_constants = [
            g.op("Constant", value_s=s)
            for s in symbolic_helper._node_get(node, "value")
        ]
        return g.op("prim::ListConstruct", *str_constants)

    raise errors.SymbolicValueError(
        f"Unsupported prim::Constant kind: '{node.kindOf('value')}'. "
        f"Please send a bug report at {_constants.PYTORCH_GITHUB_ISSUES_URL}.",
        node.output(),
    )