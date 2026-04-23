def _scatter_fused_allreduce_waits(
    graph: fx.Graph,
    fused_comm_block: CommBlock,
    orig_comm_blocks: list[CommBlock],
    node_indices: dict[fx.Node, int],
    split_and_reshape: bool = True,
) -> None:
    """
    Scatters the result of the fused communication node to the original users.
    If the fused method is concat splitting the output and reshape will be inserted,
    before inserting getitem. Otherwise getitem will be used as the users of the
    wait node.
    """

    # Before we mass up the order, we need to get the index of the last wait node
    # in orig_comm_blocks. This index will be later used to determine what users
    # nodes need to be move to maintain a correct topological sort order.
    last_wait_node_idx = 0

    for node in graph.nodes:
        last_wait_node_idx = max(
            node_indices.get(node, last_wait_node_idx), last_wait_node_idx
        )
        if node == orig_comm_blocks[-1].wait_nodes[0]:
            break

    if split_and_reshape:
        fused_wait_node = fused_comm_block.wait_nodes[0]
        with graph.inserting_after(fused_wait_node):
            split_node = call_function(
                graph,
                aten.split,
                (
                    fused_wait_node,
                    [math.prod(cast(list[int], cb.shape)) for cb in orig_comm_blocks],
                ),
            )
        with graph.inserting_after(split_node):
            fused_outputs = []
            for idx, comm_block in enumerate(orig_comm_blocks):
                split_idx_node = call_function(
                    graph, operator.getitem, (split_node, idx)
                )
                with graph.inserting_after(split_idx_node):
                    fused_outputs.append(
                        call_function(
                            graph, aten.reshape, (split_idx_node, comm_block.shape)
                        )
                    )
    else:
        fused_outputs = fused_comm_block.wait_nodes

    # Scatter the fused outputs.
    incorrect_order_nodes = []
    for comm_block, fused_output in zip(orig_comm_blocks, fused_outputs):
        # Some descendant users of the orig_comm_blocks may be scheduled before
        # the fused all_reduce. For example, the user nodes of the very first
        # all_reduce may be scheduled before the second all_reduce. Since the
        # fused all_reduce is inserted right after the last all_reduce, the
        # order can be wrong.
        # `incorrect_order_nodes` records these nodes.

        orig_wait = comm_block.wait_nodes[0]
        nodes = collections.deque(list(orig_wait.users))
        while nodes:
            user_node = nodes.popleft()
            if not isinstance(user_node, fx.Node):
                continue

            if node_indices[user_node] < last_wait_node_idx:
                incorrect_order_nodes.append(user_node)
                nodes.extend(list(user_node.users))

        orig_wait.replace_all_uses_with(fused_output)

    last_fused_result = fused_outputs[0]
    fused_outputs_set = OrderedSet(fused_outputs)
    for node in graph.nodes:
        if node in fused_outputs_set:
            last_fused_result = node

    # Move the incorrect_order_nodes to right after the last fused_result.
    incorrect_order_nodes = sorted(
        incorrect_order_nodes, key=lambda node: node_indices[node]
    )
    move_block_after(incorrect_order_nodes, last_fused_result)