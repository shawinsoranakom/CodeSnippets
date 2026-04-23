def create_n_transformed_and_logged_copies_of_subgraph(
    mt: GraphModule,
    subgraph_idx: int,
    match_name: str,
    nodes_in_this_subgraph: list[Any],
    qconfig_mappings: list[QConfigMapping],
    list_of_node_name_to_qconfig: list[dict[str, QConfigAny]],
    custom_prepare_fn: Callable | None = None,
    custom_prepare_kwargs: dict[str, Any] | None = None,
) -> None:
    """
    Given a model `mt` and a subgraph_idx, creates the needed copies
    of the subgraph for all qconfigs, and instruments them with loggers.
    """
    # for now, assume that
    # 1. the first node has one input
    # 2. the last node has one output

    # for now, ignore all subgraphs that contain non-nodes (tuples, etc)
    # TODO(future PR): implement this
    if any(not isinstance(node, Node) for node in nodes_in_this_subgraph):
        return

    first_node = nodes_in_this_subgraph[0]
    last_node = nodes_in_this_subgraph[-1]
    # We used output propagation to populate example values on each
    # node. Use the example values from the previous node as the input
    # to the current node.
    prev_node = get_normalized_nth_input(first_node, mt, 0)
    if isinstance(prev_node, list):
        example_inputs = [x.traced_result for x in prev_node]
    elif isinstance(prev_node, tuple):
        example_inputs = (x.traced_result for x in prev_node)  # type: ignore[assignment]
    else:
        # currently some customer models do not have a traced_result in
        # every node, so we have to guard for this case since we cannot
        # quantize without an example input
        # TODO(future PR): add a test case for this once we have an easy
        # repro, see https://github.com/pytorch/pytorch/pull/80521/files#r975940489
        # for additional context
        if hasattr(prev_node, "traced_result"):
            example_inputs = (prev_node.traced_result,)  # type: ignore[attr-defined, assignment]
        else:
            print(
                "unable to get example input for node "
                + f"{first_node.format_node()}, skipping"
            )
            return

    # If there are no quantization configs for this subgraph, skip adding
    # loggers. This reduces memory usage for models where not all layers are
    # quantized.
    # TODO(future): consider making this configurable
    found_at_least_one_qconfig = False
    for subgraph_candidate_idx in range(len(qconfig_mappings) + 1):
        if subgraph_candidate_idx == 0:
            # fp32 baseline does not need a qconfig
            continue

        # a. we have N shadows, so len(qconfig_mappings) is N
        # b. we will have the fp32 layer + N shadows, so overall number of
        #    (original_op) + (*shadows) will be N+1
        # c. since `subgraph_candidate_idx` represents (b), we need
        #    to subtract 1 to query from (a)
        node_name_to_qconfig = list_of_node_name_to_qconfig[subgraph_candidate_idx - 1]
        qconfig = node_name_to_qconfig[first_node.name]
        if qconfig is not None:
            found_at_least_one_qconfig = True
            break
    if not found_at_least_one_qconfig:
        print(
            "unable to find at least one qconfig for node "
            + f"{first_node.format_node()}, skipping"
        )
        return

    fqn = _maybe_get_fqn(first_node, mt)

    # We want the results to contain the subgraphs in natural order,
    # and the graph to also contain shadow wrappers and shadow loggers
    # in natural order.
    # If we just iterate in reverse, the graph will be in natural
    # order but the eventual results will be in reverse order.
    # So, we keep track of the last shadow logger we added and
    # always insert after it.
    last_added_shadow_node_list: list[Node | None] = [None]
    for subgraph_candidate_idx in range(len(qconfig_mappings) + 1):
        create_one_transformed_and_logged_copy_of_subgraph(
            mt,
            subgraph_idx,
            subgraph_candidate_idx,
            first_node,
            last_node,
            fqn,
            list_of_node_name_to_qconfig,
            example_inputs,
            last_added_shadow_node_list,
            custom_prepare_fn,
            custom_prepare_kwargs,
        )