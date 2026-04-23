def _coll_exposed_communication_time(
    collective_snode: BaseSchedulerNode,
    next_dict: dict[BaseSchedulerNode, BaseSchedulerNode | None],
    runtimes: dict[BaseSchedulerNode, float],
    node_output_sets: dict[BaseSchedulerNode, frozenset[str]],
    node_dep_sets: dict[BaseSchedulerNode, frozenset[str]],
) -> tuple[float, float, str]:
    """
    Calculate exposed communication time by iterating directly over linked list.
    Avoids O(N) list construction for each call.

    The collective_snode is the starting point, iteration continues via next_dict.
    """
    comm_time = runtimes[collective_snode]
    comp_time = 0.0
    collective_outs = node_output_sets[collective_snode]
    overlap_info = ""
    collectives_found: list[BaseSchedulerNode] = []

    snode = next_dict[collective_snode]
    while snode is not None:
        unmet_deps = node_dep_sets[snode]

        if unmet_deps & collective_outs:
            overlap_info += f"->W[{snode.get_name()}]"
            break

        if contains_collective(snode):
            if not contains_async_collective(snode):
                break
            else:
                collectives_found.append(snode)
                snode = next_dict[snode]
                continue
        if contains_wait(snode):
            has_wait_for_collectives_found = False
            for _coll in collectives_found:
                if _is_corresponding_collective_wait(
                    collective_snode, snode, node_output_sets, node_dep_sets
                ):
                    has_wait_for_collectives_found = True
                    break
            if has_wait_for_collectives_found:
                break

        comp_time_before = comp_time

        def accumulate_time(_snode: BaseSchedulerNode) -> None:
            nonlocal comp_time
            comp_time += runtimes[_snode]

        _temp_group_visit_leaves(snode, accumulate_time)
        comp_time_after = comp_time
        overlap_info += f"+{snode.get_name()}[{comp_time_after - comp_time_before}]"

        snode = next_dict[snode]

    return comm_time, comp_time, overlap_info