def _sequential_split_and_maybe_inline_subgraphs_helper(
    new_gm: torch.fx.GraphModule,
    graph_signature: ExportGraphSignature | None,
    maybe_inline_or_replace_with_hop: Callable[[torch.fx.Node], None],
) -> tuple[torch.fx.GraphModule, ExportGraphSignature | None]:
    """
    Helper function for replacing graph nodse with higher order nodes.
    For each subgraph in `new_gm`, decides whether to construct a HOO subgraph, or inline the calls
    back into the parent graph module, depending on `maybe_inline_or_replace_with_hop`.
    """
    # new_gm is a new graph module that could have different output args names.
    # We need to fix the graph signature.
    replace_ctx = contextlib.nullcontext()
    new_signature = None
    if graph_signature is not None:
        # Cannot deep copy a real ScriptObject, which is referenced
        # in the FakeScriptObject. Copy should be good enough to guard
        # against accidental mutation to original graph_signature.
        new_signature = copy.copy(graph_signature)
        new_gm_out_node = next(reversed(new_gm.graph.find_nodes(op="output")))
        if new_gm_out_node.op != "output" or len(new_gm_out_node.args[0]) != len(
            new_signature.output_specs
        ):
            raise AssertionError(
                f"output node mismatch: {new_gm_out_node.op}, "
                f"{len(new_gm_out_node.args[0])} vs {len(new_signature.output_specs)}"
            )
        for arg_node, out_spec in zip(
            new_gm_out_node.args[0], new_signature.output_specs
        ):
            if arg_node is None:
                if out_spec.arg.value is not None:  # type: ignore[union-attr]
                    raise AssertionError(
                        f"expected None out_spec.arg.value, got {out_spec.arg.value}"  # type: ignore[union-attr]
                    )
            elif (
                isinstance(arg_node, torch.fx.Node)
                and out_spec.arg.name != arg_node.name
            ):
                out_spec.arg.name = arg_node.name

        replace_ctx = new_gm._set_replace_hook(new_signature.get_replace_hook())  # type: ignore[assignment]

    with replace_ctx:
        nodes_map(
            list(new_gm.graph.nodes),
            lambda node: (
                maybe_inline_or_replace_with_hop(node)
                if node.op == "call_module"
                else node
            ),
        )
    new_gm.recompile()
    new_gm.graph.lint()
    return new_gm, new_signature