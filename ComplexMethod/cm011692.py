def init_group_node(
    group_snode: FusedSchedulerNode | GroupedSchedulerNode,
    scheduler: Scheduler,
    snodes: list[BaseSchedulerNode],
) -> None:
    assert isinstance(group_snode, (FusedSchedulerNode, GroupedSchedulerNode))
    group_snode.snodes = snodes
    group_snode.scheduler = scheduler
    group_snode.node = None
    group_snode.ancestors = OrderedSet.union(
        *[x.ancestors for x in snodes if x.ancestors is not None]
    )

    refresh_group_node_dependencies(group_snode)

    group_snode.min_order = min(x.min_order for x in group_snode.snodes)
    group_snode.max_order = max(x.max_order for x in group_snode.snodes)
    group_snode.min_input_distance = min(
        x.min_input_distance for x in group_snode.snodes
    )
    group_snode.max_input_distance = max(
        x.max_input_distance for x in group_snode.snodes
    )
    group_snode.outputs_by_name = {
        buf.get_name(): buf for buf in group_snode.get_outputs()
    }