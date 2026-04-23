def remove_fsdp2_unsharded_param_graph_input_usage(graph: torch.fx.Graph):
    """
    This FX graph pass replaces uses of FSDP2 unsharded params with their corresponding
    graph intermediates that were fsdp.copy_ into the unsharded params in the original graph.

    NOTE: Can only apply this pass to any of the FSDP2 unsharded params that have this pattern
    (or repetition of): `resize_(full) -> copy_ -> resize_(0)`. Because of this, for partial-graph case
    where `resize_(full) -> copy_` is in one graph and `resize_(0)` is in another graph, we can't
    remove these resize and copy ops and thus we will have worse performance there.

    In other words, "do we try to remove all the resize_(full) -> copy_ -> resize_(0) nodes for this unsharded param"
    is actually a per-unsharded-param decision, since for each unsharded param, we look at its resize sequence pattern
    (in `check_resize_pattern()`) to determine if its set of resize and copy nodes can be removed.
    """
    node_list = list(graph.nodes)

    # Find all graph inputs and their resize counts
    graph_input_to_resized_to_full_node_idxes = defaultdict(list)
    graph_input_to_resized_to_0_node_idxes = defaultdict(list)
    for idx, node in enumerate(node_list):
        if (
            node.op == "call_function"
            and node.target is torch.ops.inductor.resize_storage_bytes_.default
        ):
            assert node.args[0].op == "placeholder", f"""\
Resize can only operate on graph inputs, but got {node} which is resizing non-graph-input {node.args[0]}
"""
            graph_input = node.args[0]
            new_size = node.args[1]
            if new_size > 0:
                graph_input_to_resized_to_full_node_idxes[graph_input].append(idx)
            else:
                graph_input_to_resized_to_0_node_idxes[graph_input].append(idx)

    def check_resize_pattern(graph_input):
        # Check the number of resize-to-full and resize-to-0 nodes are equal,
        # and that for each (resize-to-full, resize-to-0) pair, the resize-to-full node
        # always happens before the resize-to-0 node.
        # This is the precondition for being able to remove all the resize and copy nodes
        # for this specific unsharded param.
        resized_to_full_idxes = graph_input_to_resized_to_full_node_idxes.get(
            graph_input, []
        )
        resized_to_0_idxes = graph_input_to_resized_to_0_node_idxes.get(graph_input, [])

        if len(resized_to_full_idxes) != len(resized_to_0_idxes):
            log.warning(
                f"""
Unequal number of resize-to-full and resize-to-0 nodes for graph input {graph_input}:
{len(resized_to_full_idxes)} vs. {len(resized_to_0_idxes)}.
Skipping `remove_fsdp2_unsharded_param_graph_input_usage` FX graph pass.
"""  # noqa: G004
            )
            return False

        # Check the sequence: (resize_to_full -> resize_to_0)+
        for resize_to_full_idx, resize_to_0_idx in zip(
            resized_to_full_idxes, resized_to_0_idxes
        ):
            if resize_to_full_idx >= resize_to_0_idx:
                log.warning(
                    f"""
For graph input {graph_input}: resize-to-full node {node_list[resize_to_full_idx]} at index {resize_to_full_idx}
happens after resize-to-0 node {node_list[resize_to_0_idx]} at index {resize_to_0_idx}.
Skipping `remove_fsdp2_unsharded_param_graph_input_usage` FX graph pass for that unsharded param.
"""  # noqa: G004
                )
                return False
        return True

    # Find all eligible unsharded params and their corresponding graph intermediates.
    unsharded_param_to_fsdp_copy_node_idxes = defaultdict(list)
    for idx, node in enumerate(node_list):
        if node.op == "call_function" and node.target is torch.ops.fsdp.copy_.default:
            fsdp_copy_node = node
            unsharded_param = node.args[0]
            assert unsharded_param.op == "placeholder", f"""
Assumed all FSDP2 `unsharded_param`s to be graph input, but it's not true!
Offending node: {unsharded_param}. Graph: {graph}
"""
            if check_resize_pattern(unsharded_param):
                unsharded_param_to_fsdp_copy_node_idxes[unsharded_param].append(idx)

    def is_allowed_mutation(node):
        return (
            node.target is torch.ops.fsdp.copy_.default
            or node.target is torch.ops.inductor.resize_storage_bytes_.default
        )

    def is_node_mutating_unsharded_param_or_its_alias(node, unsharded_params):
        # Check whether the node is mutating any of the unsharded params or their aliases.
        mutated_arg_idxes = (
            [
                i
                for i, x in enumerate(node.target._schema.arguments)
                if x.alias_info is not None and x.alias_info.is_write
            ]
            if isinstance(node.target, torch._ops.OpOverload)
            else []
        )
        mutated_node_arg_storages = OrderedSet(
            [
                StorageWeakRef(node.args[i].meta["val"].untyped_storage())
                for i in mutated_arg_idxes
            ]
        )
        storages_of_unsharded_params = OrderedSet(
            [
                StorageWeakRef(unsharded_param.meta["val"].untyped_storage())
                for unsharded_param in unsharded_params
            ]
        )
        return len(mutated_node_arg_storages & storages_of_unsharded_params) > 0

    # Check no user mutation on any unsharded_param
    for node in node_list:
        if (
            node.op == "call_function"
            and isinstance(node.target, torch._ops.OpOverload)
            and node.target._schema.is_mutable
            and not is_allowed_mutation(node)
        ):
            assert not is_node_mutating_unsharded_param_or_its_alias(
                node, unsharded_param_to_fsdp_copy_node_idxes.keys()
            ), f"""\
User mutation on FSDP2 unsharded param is not allowed when Traceable FSDP2 is used. Violating node: {node}
"""

    # For each `fsdp.copy_(unsharded_param, Y)`, replace downstream usage of `unsharded_param` with `Y`.
    #
    # NOTE: Because of "layer reuse" use case, there could be multiple `fsdp.copy_` to the same `unsharded_param` graph input.
    # e.g.
    # ```
    #     fsdp_copy_1 = fsdp.copy_(unsharded_param_1, Y1)
    #     ... (use of unsharded_param_1)                     -> Subgraph 1
    #     fsdp_copy_2 = fsdp.copy_(unsharded_param_1, Y2)
    #     ... (use of unsharded_param_1)                     -> Subgraph 2
    #     fsdp_copy_3 = fsdp.copy_(unsharded_param_1, Y3)
    #     ... (use of unsharded_param_1)                     -> Subgraph 3
    # ```
    # We must do the replacement only within each subgraph.
    for (
        unsharded_param,
        fsdp_copy_node_idxes,
    ) in unsharded_param_to_fsdp_copy_node_idxes.items():
        for i, fsdp_copy_node_idx in enumerate(fsdp_copy_node_idxes):
            fsdp_copy_node = node_list[fsdp_copy_node_idx]
            assert fsdp_copy_node.args[0] is unsharded_param
            _, replacement = fsdp_copy_node.args
            # subgraph_start_idx is exclusive
            subgraph_start_idx = fsdp_copy_node_idx + 1
            # subgraph_end_idx is exclusive (also intentionally don't replace args in return op)
            subgraph_end_idx = (
                fsdp_copy_node_idxes[i + 1]
                if i < len(fsdp_copy_node_idxes) - 1
                else len(node_list) - 1
            )
            subgraph_nodes = node_list[subgraph_start_idx:subgraph_end_idx]
            assert not any(
                is_node_mutating_unsharded_param_or_its_alias(node, [unsharded_param])
                for node in subgraph_nodes
            ), f"""\
Assumed no ops mutating unsharded param {unsharded_param} in subgraph {subgraph_nodes}, but it's not true!
Graph: {graph}
"""
            for node in subgraph_nodes:
                if (
                    node.op == "call_function"
                    and unsharded_param in node.args
                    and node.target != torch.ops.inductor.resize_storage_bytes_.default
                ):  # TODO(yf225): implement replacement in kwargs
                    new_args = tuple(
                        replacement if arg is unsharded_param else arg
                        for arg in node.args
                    )
                    node.args = new_args

    # Delete `fsdp.copy_(unsharded_param, Y)` nodes
    for fsdp_copy_node_idxes in unsharded_param_to_fsdp_copy_node_idxes.values():
        for fsdp_copy_node_idx in fsdp_copy_node_idxes:
            fsdp_copy_node = node_list[fsdp_copy_node_idx]
            graph.erase_node(fsdp_copy_node)

    # Delete `resize_(unsharded_param, ...)` nodes
    for node in node_list:
        if (
            node.op == "call_function"
            and node.target is torch.ops.inductor.resize_storage_bytes_.default
            and node.args[0] in unsharded_param_to_fsdp_copy_node_idxes
        ):
            graph.erase_node(node)