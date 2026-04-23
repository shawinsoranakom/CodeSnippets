def permute_matmul_fusion(module: torch.fx.GraphModule) -> torch.fx.GraphModule:
    for node in itertools.chain(
        module.graph.find_nodes(op="call_function", target=torch.bmm),
        module.graph.find_nodes(op="call_function", target=torch.matmul),
    ):
        normalized = NormalizedMatmulNode(node)
        input_A_node = normalized.get_input()
        input_B_node = normalized.get_other()
        input_A = input_A_node
        input_B = input_B_node
        Atrans = Btrans = False
        if (
            input_A_node.op == "call_method"
            and input_A_node.target == "permute"
            and check_permute(input_A_node)
        ):
            Atrans = True
            if len(input_A_node.args) > 0:
                input_A = input_A_node.args[0]  # type: ignore[assignment]
            else:
                input_A = input_A_node.kwargs["input"]  # type: ignore[assignment]

        if (
            input_B_node.op == "call_method"
            and input_B_node.target == "permute"
            and check_permute(input_B_node)
        ):
            Btrans = True
            if len(input_B_node.args) > 0:
                input_B = input_B_node.args[0]  # type: ignore[assignment]
            else:
                input_B = input_B_node.kwargs["input"]  # type: ignore[assignment]

        if Atrans or Btrans:
            with module.graph.inserting_before(node):
                fused_node = module.graph.call_function(
                    transpose_matmul,
                    args=(input_A, input_B, Atrans, Btrans),
                )
            node.replace_all_uses_with(fused_node)
            module.graph.erase_node(node)
            if Atrans and len(input_A_node.users) == 0:
                module.graph.erase_node(input_A_node)
            if Btrans and len(input_B_node.users) == 0:
                module.graph.erase_node(input_B_node)

    module.graph.lint()
    module.recompile()
    return module