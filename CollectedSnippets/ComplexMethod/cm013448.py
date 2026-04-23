def _inline_module(
    gm: torch.fx.GraphModule, inline_mod_name: str, run_dce: bool = True
) -> dict[torch.fx.Node, torch.fx.Node]:
    """
    Given `gm` and some graph module which is called with target name `inline_mod_name`,
    this helper will inline all of the nodes from that called graph module into `gm`.

    Returns a mapping from subgraph nodes to the newly created/mapped nodes in gm.
    """
    # Fetch the inner graph module that we want to inline inside `gm`.
    inline_mod = dict(gm.named_modules())[inline_mod_name]
    if not isinstance(inline_mod, torch.fx.GraphModule):
        raise AssertionError(f"Expected GraphModule, got {type(inline_mod)}")
    call_mod_node_to_replace = None
    for node in gm.graph.nodes:
        if node.op == "call_module" and node.target == inline_mod_name:
            call_mod_node_to_replace = node
            break
    if call_mod_node_to_replace is None:
        raise AssertionError(f"Could not find call_module node for {inline_mod_name}")

    # Now actually do the swap. Note that we have to keep track of new nodes that are
    # copied into `gm` -- we do this via replacement_mapping.
    call_mod_args = call_mod_node_to_replace.args
    call_mod_kwargs = call_mod_node_to_replace.kwargs

    replacement_mapping: dict[torch.fx.Node, torch.fx.Node] = {}
    ph_count = 0

    def replacement_fn(node: torch.fx.Node) -> torch.fx.Node:
        new_node = replacement_mapping[node]
        new_node.meta = node.meta.copy()
        return new_node

    for inline_node in inline_mod.graph.nodes:
        if inline_node.op == "placeholder":
            replacement_mapping[inline_node] = (
                call_mod_kwargs[inline_node.name]
                if inline_node.name in call_mod_kwargs
                else call_mod_args[ph_count]
            )

            ph_count += 1
            continue

        if inline_node.op == "output":
            outputs = inline_node.args[0]
            output_replacements = map_arg(outputs, replacement_fn)

            # If output is a tuple, we need to handle getitem users specially.
            # Capture users before replace_all_uses_with modifies them.
            getitem_users: list[torch.fx.Node] = []
            if isinstance(output_replacements, (list, tuple)):
                import operator

                getitem_users = [
                    user
                    for user in call_mod_node_to_replace.users
                    if user.op == "call_function"
                    and user.target is operator.getitem
                    and isinstance(user.args[1], int)
                ]

            call_mod_node_to_replace.replace_all_uses_with(output_replacements)

            # Inline getitem nodes that now index into the tuple literal
            for user in getitem_users:
                idx = user.args[1]
                if not isinstance(idx, int):
                    raise AssertionError(f"Expected int index, got {type(idx)}")
                user.replace_all_uses_with(output_replacements[idx])
                gm.graph.erase_node(user)
                replacement_mapping[user] = output_replacements[idx]

            continue

        with gm.graph.inserting_before(call_mod_node_to_replace):
            new_node = gm.graph.node_copy(inline_node, replacement_fn)
        replacement_mapping[inline_node] = new_node

    # Explicitly remove the module that was just inlined,
    # this module may contain impure ops so cannot be dead code eliminated,
    # this module is unneeded as it's just inlined back to main graph.
    gm.graph.erase_node(call_mod_node_to_replace)
    if run_dce:
        gm.graph.eliminate_dead_code()

    return replacement_mapping