def cast_dtype_args_to_fp64(model: torch.fx.GraphModule) -> torch.fx.GraphModule:
    for node in model.graph.nodes:
        if (
            node.op == "call_function"
            and node.target is torch.ops.prims.convert_element_type.default
        ):
            assert len(node.args) == 2
            if is_float_dtype(node.args[1]) and node.args[1] != torch.float64:
                node.args = (node.args[0], torch.float64)
        if node.op == "call_function":
            dtype = node.kwargs.get("dtype")
            if dtype is not None and is_float_dtype(dtype):
                new_kwargs = dict(node.kwargs)
                new_kwargs["dtype"] = torch.float64
                node.kwargs = new_kwargs

    model.graph.lint()
    model.recompile()
    return model