def schedule_comm_wait(graph: fx.Graph) -> None:
    """
    Delay the execution of wait tensors of allreduce until its first user.

    This algorithm considers the intermediate users, like split, getitem,
    of the wait node and schedule those intermediate users as well.
    This will result in a better overlapping result.
    """
    ops = (
        torch.ops._c10d_functional.all_reduce_.default,
        torch.ops._c10d_functional.all_reduce.default,
        torch.ops._c10d_functional.all_reduce_coalesced.default,
        torch.ops._c10d_functional.all_reduce_coalesced_.default,
    )
    comm_blocks = get_all_comm_blocks(graph, ops)
    if not comm_blocks:
        return

    # Find all the end users.
    allreduce_users = OrderedSet[fx.Node]()
    for allreduce in comm_blocks:
        for output in allreduce.outputs:
            allreduce_users.update(output.users)

    node_indices = {node: i for i, node in enumerate(graph.nodes)}
    for allreduce in comm_blocks:
        # Find the earliest/first user -- target_node.
        assert len(allreduce.outputs) >= 1, (
            f"Found a allreduce that has zero outputs/users -- {allreduce}."
        )
        # Initialize the target node to avoid typing issues.
        target_node = next(iter(next(iter(allreduce.outputs)).users))
        target_node_index = 2**31
        for user in (user for output in allreduce.outputs for user in output.users):
            index = node_indices[user]
            if index < target_node_index:
                target_node = user
                target_node_index = index

        # Move wait nodes and all the subsequent nodes in the comm_block to
        # before the first user -- target_node.
        wait_idx = -1
        for wait_idx, node in enumerate(allreduce.node_list):
            if node == allreduce.wait_nodes[0]:
                break
        assert wait_idx >= 0
        move_block_before(allreduce.node_list[wait_idx:], target_node)