def is_mutation_op(node: torch.fx.Node) -> bool:
    if isinstance(
        node.target, torch._ops.OpOverload
    ) and not fixme_incorrect_inductor_schema_op(node.target):
        return node.target._schema.is_mutable
    elif isinstance(
        node.target, torch._higher_order_ops.auto_functionalize.AutoFunctionalized
    ):
        return False
    if node.op == "call_function":
        assert callable(node.target)
        if _mutation_op_re.search(node.target.__name__):
            return True
    elif node.op == "call_method":
        assert isinstance(node.target, str)
        if _mutation_op_re.search(node.target):
            return True
    return node.kwargs.get("out") is not None