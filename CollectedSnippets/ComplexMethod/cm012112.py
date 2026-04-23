def _wait_exposed_communication_time(
    wait_snode: BaseSchedulerNode,
    head: BaseSchedulerNode,
    prev_dict: dict[BaseSchedulerNode, BaseSchedulerNode | None],
    runtimes: dict[BaseSchedulerNode, float],
    node_output_sets: dict[BaseSchedulerNode, frozenset[str]],
    node_dep_sets: dict[BaseSchedulerNode, frozenset[str]],
) -> tuple[float, float, str]:
    """
    Calculate exposed communication time for a wait operation by iterating
    directly over linked list backwards. Avoids O(N) list construction.

    Iterates from wait_snode backwards using prev_dict to find corresponding collective.
    """
    comm_time = 0.0
    comp_time = 0.0
    overlap_info = ""
    waits_found: list[BaseSchedulerNode] = []

    snode = prev_dict[wait_snode]
    while snode is not None:
        if contains_wait(snode):
            waits_found.append(snode)
        if contains_collective(snode):
            if _is_corresponding_collective_wait(
                snode, wait_snode, node_output_sets, node_dep_sets
            ):
                comm_time = runtimes[snode]
                overlap_info += f"->C[{snode.get_name()}]"
                break

            if not contains_async_collective(snode):
                comp_time = 0.0
                snode = prev_dict[snode]
                continue
            else:
                for w in waits_found:
                    if _is_corresponding_collective_wait(
                        snode, w, node_output_sets, node_dep_sets
                    ):
                        comp_time = 0.0
                        break  # inner loop break
                snode = prev_dict[snode]
                continue

        comp_time_before = comp_time

        def accumulate_time(_snode: BaseSchedulerNode) -> None:
            nonlocal comp_time
            comp_time += runtimes[_snode]

        _temp_group_visit_leaves(snode, accumulate_time)
        comp_time_after = comp_time
        overlap_info += f"+{snode.get_name()}[{comp_time_after - comp_time_before}]"

        snode = prev_dict[snode]

    return comm_time, comp_time, overlap_info