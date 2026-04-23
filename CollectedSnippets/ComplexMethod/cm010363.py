def check_input_alias_and_mutation_return_outputs(
    gm: torch.fx.GraphModule,
) -> tuple[
    dict[int, int],
    dict[int, int],
    dict[int, int],
    list[int],
    tuple[Any, ...] | list[Any],
]:
    def _get_example_value(n):
        if not isinstance(n, torch.fx.Node):
            return n
        if "val" in n.meta:
            return n.meta["val"]
        if "example_value" in n.meta:
            return n.meta["example_value"]
        return None

    fake_args = [
        _get_example_value(n)
        for n in gm.graph.find_nodes(op="placeholder")
        if isinstance(n, torch.fx.Node) and "val" in n.meta
    ]
    outputs = [
        _get_example_value(n)
        for n in pytree.tree_flatten(gm.graph.find_nodes(op="output")[0].args[0])[0]
    ]

    # We need to analyze the original fake_args to detect
    # inp-inp alias.
    inp_storage_map = {
        _tensor_storage(inp): i
        for i, inp in enumerate(fake_args)
        if isinstance(inp, torch.Tensor)
    }
    out_storage_map = {
        _tensor_storage(out): i
        for i, out in enumerate(outputs)
        if isinstance(out, torch.Tensor)
    }
    inp_inp_alias_map = {
        i: inp_storage_map[_tensor_storage(inp)]
        for i, inp in enumerate(fake_args)
        if isinstance(inp, torch.Tensor) and inp_storage_map[_tensor_storage(inp)] != i
    }
    out_out_alias_map = {
        i: out_storage_map[_tensor_storage(out)]
        for i, out in enumerate(outputs)
        if isinstance(out, torch.Tensor) and out_storage_map[_tensor_storage(out)] != i
    }
    inp_out_alias_map = {
        i: out_storage_map[_tensor_storage(inp)]
        for i, inp in enumerate(fake_args)
        if isinstance(inp, torch.Tensor) and _tensor_storage(inp) in out_storage_map
    }
    mutated_inputs = []
    for node in gm.graph.nodes:
        if node.op == "call_function" and isinstance(
            node.target, torch._ops.OpOverload
        ):
            for arg_node, arg_schema in zip(node.args, node.target._schema.arguments):
                if arg_schema.is_write:
                    arg_val = _get_example_value(arg_node)
                    if not isinstance(arg_val, torch.Tensor):
                        raise AssertionError(
                            f"Expected arg_val to be a Tensor, got {type(arg_val)}"
                        )
                    if _tensor_storage(arg_val) in inp_storage_map:
                        mutated_inputs.append(inp_storage_map[_tensor_storage(arg_val)])

    return (
        inp_inp_alias_map,
        inp_out_alias_map,
        out_out_alias_map,
        mutated_inputs,
        outputs,
    )