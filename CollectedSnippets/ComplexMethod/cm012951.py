def get_linear_fun_weight(node: Node, gm: GraphModule) -> torch.Tensor:
    # traverse backwards from the weight arg, accounting for any observers
    # supported patterns:
    # weight -> obs -> linear
    # weight -> to(torch.float16) -> dequantize -> linear
    linear_second_arg = node.args[1]
    if not isinstance(linear_second_arg, Node):
        raise AssertionError(f"Expected Node, got {type(linear_second_arg)}")

    if linear_second_arg.op == "call_module":
        # weight -> obs -> linear
        weight_arg_node = node.args[1]
        if not isinstance(weight_arg_node, Node):
            raise AssertionError(f"Expected Node, got {type(weight_arg_node)}")
        weight_node = weight_arg_node.args[0]
        if not isinstance(weight_node, Node):
            raise AssertionError(f"Expected Node, got {type(weight_node)}")
        if weight_node.op != "get_attr":
            raise AssertionError(f"Expected get_attr, got {weight_node.op}")
        weight = getattr_from_fqn(gm, weight_node.target)  # type: ignore[arg-type]
        return weight.detach()
    elif linear_second_arg.op == "call_method":
        # weight -> to(torch.float16) -> dequantize -> linear
        if linear_second_arg.op != "call_method":
            raise AssertionError(f"Expected call_method, got {linear_second_arg.op}")
        dequant_node = node.args[1]
        if not isinstance(dequant_node, Node):
            raise AssertionError(f"Expected Node, got {type(dequant_node)}")
        to_fp16_node = dequant_node.args[0]
        if not isinstance(to_fp16_node, Node):
            raise AssertionError(f"Expected Node, got {type(to_fp16_node)}")
        # extract the dtype, so we can cast to it before returning
        target_dtype = to_fp16_node.args[1]
        weight_node = to_fp16_node.args[0]
        if not isinstance(weight_node, Node):
            raise AssertionError(f"Expected Node, got {type(weight_node)}")
        if weight_node.op != "get_attr":
            raise AssertionError(f"Expected get_attr, got {weight_node.op}")
        weight = getattr_from_fqn(gm, weight_node.target)  # type: ignore[arg-type]
        # return the weight with fp16 cast
        return weight.detach().to(target_dtype)
    else:
        if linear_second_arg.op != "get_attr":
            raise AssertionError(f"Expected get_attr, got {linear_second_arg.op}")
        weight = getattr_from_fqn(gm, linear_second_arg.target)  # type: ignore[arg-type]
        return weight.detach()