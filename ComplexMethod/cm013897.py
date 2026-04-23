def _replace_region_with_subgraph(
    graph: torch.fx.Graph,
    region: Region,
    get_subgraph_node: Node,
    external_node_usages: Iterable[OrderedSet[UsageIndex]],
    node_usage_to_tuple_elems: dict[UsageIndex, OrderedSet[int]],
    ind_to_tuple_spec: dict[int, dict[tuple[int, ...], int]],
    inds_with_external_users: list[int],
    subgraph_name: str,
    node_to_additional_deps: dict[Node, OrderedSet[Node]],
    node_to_mutated_arg_positions: dict[Node, OrderedSet[int]],
) -> None:
    sub_args = []
    flattened_getitem_nodes: OrderedSet[Node] = OrderedSet()
    for usages in external_node_usages:
        usage = next(iter(usages))
        node_ind, usage_ind = usage
        node = region[node_ind]
        flattened_args_kwargs = _get_flat_args(node, {})
        for user_ind, node_usage_ind in usages:
            user = region[user_ind]
            if user in node_to_mutated_arg_positions:
                if node_usage_ind in node_to_mutated_arg_positions[user]:
                    log.debug(
                        "NYI: Failed to substitute region %s due to mutation", region
                    )
                    return
        if usage in node_usage_to_tuple_elems:
            tuple_elems = [region[i] for i in node_usage_to_tuple_elems[usage]]
            flattened_getitem_nodes.update(tuple_elems)
            sub_args.extend(tuple_elems)
        else:
            sub_args.append(flattened_args_kwargs[usage_ind])

    # Input/Output aliasing not supported in HOPs today
    # Note: we should use the nodes in the original graph (the region here)
    # because we use the original traced example values for this check
    if _has_aliasing(
        region, sub_args, inds_with_external_users, flattened_getitem_nodes
    ):
        return

    invoke_args = (get_subgraph_node, subgraph_name, *sub_args)

    invoke_subgraph_node = graph.create_node(
        "call_function",
        torch.ops.higher_order.invoke_subgraph,
        invoke_args,  # type: ignore[arg-type]
        {},
    )

    ind = 0
    flattened_output_nodes: OrderedSet[Node] = OrderedSet()
    for external_user_ind in inds_with_external_users:
        node = region[external_user_ind]
        if _is_tuple_node(node):
            tuple_spec = ind_to_tuple_spec[external_user_ind]
            flattened_output_nodes.update(
                _replace_tuple_outputs(
                    node, ind, tuple_spec, invoke_subgraph_node, graph
                )
            )
            ind += len(tuple_spec)
        else:
            subgraph_output = graph.create_node(
                "call_function", operator.getitem, (invoke_subgraph_node, ind), {}
            )
            node.replace_all_uses_with(subgraph_output, propagate_meta=True)
            ind += 1

    # Erase in reverse topological order
    for node in reversed(region):
        if node in flattened_getitem_nodes:
            # Don't erase these, since they will still be used
            continue

        if node not in flattened_output_nodes:
            graph.erase_node(node)

        # Remove any nodes with additional deps
        # This is safe; we've guaranteed that there is
        # no input mutation, so all additional deps
        # will be internal to the subgraph
        node_to_additional_deps.pop(node, None)
        for deps in node_to_additional_deps.values():
            try:
                deps.remove(node)
                deps.add(invoke_subgraph_node)
            except KeyError:
                pass

    if config.graph_deduplication_lint:
        print(_detect_cycles(graph, node_to_additional_deps))
        _stable_topological_sort(graph, node_to_additional_deps)
        graph.lint()