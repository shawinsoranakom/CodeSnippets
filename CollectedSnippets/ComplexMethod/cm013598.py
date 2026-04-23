def get_node_target(
    submodules: Mapping[str, torch.nn.Module], node: torch.fx.Node
) -> str:
    """
    Given a `node` returns its target typename.

    For "call_method" node, return node.target which is the name of that method being called.
    This could potential lead to conflict but should be okay because normally it's on a tensor.

    For "call_function" node, return typename of node.target.

    For "call_module" node, return typename of the module that node.target point to.

    If seeing "_VariableFunctionsClass" in the target name string, it will be replaced by
    "torch". e.g. _VariableFunctionsClass.relu would become torch.relu.
    """

    if node.op not in CALLABLE_NODE_OPS:
        raise AssertionError(
            "Expect op types of "
            + ", ".join(CALLABLE_NODE_OPS)
            + f", but found {node.op}"
        )

    if node.op == "call_module":
        if not isinstance(node.target, str):
            raise AssertionError(f"Expected str target, got {type(node.target)}")
        submod = submodules[node.target]
        submod_type = getattr(submod, "_base_class_origin", type(submod))
        return get_acc_ops_name(submod_type)
    elif node.op == "call_function":
        target: Any = node.target
        return (
            f"acc_ops.{target.__name__}"
            if target.__module__ is not None and "acc_ops" in target.__module__
            else _get_qualified_name(target)
        )
    else:
        if not isinstance(node.target, str):
            raise AssertionError(f"Expected str target, got {type(node.target)}")
        return node.target