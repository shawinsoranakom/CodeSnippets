def create_grouped_node_for_allreduce_and_its_deps(snodes):
    name_to_snode = {snode.node.name: snode for snode in snodes}
    all_reduce_snodes = [
        snode
        for snode in snodes
        if isinstance(snode.node, ir._CollectiveKernel)
        and snode.node.op_overload == torch.ops._c10d_functional.all_reduce_.default
    ]
    if len(all_reduce_snodes) != 1:
        raise AssertionError(
            f"Expected exactly 1 all_reduce_snode, got {len(all_reduce_snodes)}"
        )
    all_reduce_snode = all_reduce_snodes[0]
    all_reduce_dep_snodes = [
        name_to_snode[node.name] for node in all_reduce_snode.node.inputs
    ]
    if len(all_reduce_dep_snodes) != 1:
        raise AssertionError(
            f"Expected exactly 1 all_reduce_dep_snode, got {len(all_reduce_dep_snodes)}"
        )
    all_reduce_dep_snode = all_reduce_dep_snodes[0]

    grouped_snode = scheduler.GroupedSchedulerNode.create(
        [all_reduce_dep_snode, all_reduce_snode]
    )
    new_snode_order = []
    new_snode_order.append(grouped_snode)
    for snode in snodes:
        if snode in grouped_snode.snodes:
            continue
        new_snode_order.append(snode)
    return new_snode_order