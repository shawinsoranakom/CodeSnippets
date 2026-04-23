def insert_subgm(
    gm: GraphModule,
    sub_gm: GraphModule,
    orig_inputs: tuple[Node, ...],
    orig_outputs: tuple[Node, ...],
    insertion_point: Node | None = None,
) -> GraphModule:
    # add sub_gm into gm
    submodule_name = sub_gm.__class__.__name__
    gm.add_submodule(submodule_name, sub_gm)

    # Use provided insertion point, or fall back to last output node for backwards compat
    if insertion_point is None:
        for node in reversed(gm.graph.nodes):
            if node in orig_outputs:
                insertion_point = node
                break
        if insertion_point is None:
            raise AssertionError(
                "Cannot determine insertion point: no insertion_point provided and "
                "orig_outputs is empty. Pass the last partition node as insertion_point."
            )

    # Create a call_module node in main graph.
    with gm.graph.inserting_after(insertion_point):
        module_node = gm.graph.call_module(
            submodule_name, args=orig_inputs, kwargs=None
        )
        output_node = sub_gm.graph.output_node()

    # Replace uses of original outputs with the fused module outputs.
    # If there are no external outputs, skip replacement (nothing to replace).
    if orig_outputs:
        next_node = module_node.next
        with gm.graph.inserting_before(next_node):
            if len(orig_outputs) == 1 and not isinstance(output_node.args[0], tuple):
                # main_remapping[comp.orig_outputs[0]] = module_node
                orig_outputs[0].replace_all_uses_with(module_node, propagate_meta=True)
            else:
                for i, orig_output in enumerate(orig_outputs):
                    # Use Proxy to record getitem access.
                    proxy_out = torch.fx.Proxy(module_node)[i].node  # type: ignore[index]
                    orig_output.replace_all_uses_with(proxy_out, propagate_meta=True)

                module_node.meta["val"] = tuple(
                    orig_output.meta.get("val", None) for orig_output in orig_outputs
                )
    return gm