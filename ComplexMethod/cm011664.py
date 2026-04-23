def find_recursive_users_of_node(
    snode: BaseSchedulerNode,
    collected_node_set: MutableSet[BaseSchedulerNode],
    name_to_buf: dict[str, SchedulerBuffer],
    name_to_fused_node: dict[str, BaseSchedulerNode],
    criteria_cb: Callable[[Any], bool] = lambda snode: False,
) -> None:
    if criteria_cb(snode):
        return
    collected_node_set.add(snode)
    for o in snode.get_outputs():
        for user in o.users:
            assert user.node is not None
            if user.node.get_name() == "OUTPUT":
                continue
            if user.node.get_name() not in name_to_fused_node:
                continue
            user_op = name_to_fused_node[user.node.get_name()]
            if user_op in collected_node_set:
                continue
            find_recursive_users_of_node(
                user_op,
                collected_node_set,
                name_to_buf,
                name_to_fused_node,
                criteria_cb=criteria_cb,
            )