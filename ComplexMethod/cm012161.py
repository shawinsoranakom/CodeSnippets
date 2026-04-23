def _fuse_allreduce(
    graph: fx.Graph,
    comm_blocks: list[CommBlock],
    node_indices: dict[fx.Node, int],
    use_concat: bool,
) -> CommBlock:
    """Given a list of allreduce CommBlock, fuse the CommBlocks into one CommBlock."""

    if len(comm_blocks) == 1:
        return comm_blocks[0]

    # Find the last input node of all the CommBlocks. This node will be served
    # as the inserting point of the new collective op.
    last_input_node = comm_blocks[0].inputs[0]
    last_input_index = -1
    all_input_nodes = []
    for comm_block in comm_blocks:
        input_node = comm_block.inputs[0]
        all_input_nodes.append(input_node)
        index = node_indices[input_node]
        if index >= last_input_index:
            assert index != last_input_index
            last_input_node = input_node
            last_input_index = index

    if use_concat:
        fused_comm_block = _fuse_allreduce_by_concat(
            graph, last_input_node, all_input_nodes, comm_blocks[-1]
        )
    else:
        fused_comm_block = _fuse_with_coalesced_op(
            graph, last_input_node, all_input_nodes, comm_blocks[-1]
        )

    _scatter_fused_allreduce_waits(
        graph, fused_comm_block, comm_blocks, node_indices, split_and_reshape=use_concat
    )

    for comm_block in comm_blocks:
        for wait in comm_block.wait_nodes:
            graph.erase_node(wait)
        graph.erase_node(comm_block.comm_node)
    graph.eliminate_dead_code()

    return fused_comm_block