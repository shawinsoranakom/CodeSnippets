def _reorder_communication_preserving_peak_memory_internal(
    snodes: list[BaseSchedulerNode],
) -> tuple[list[BaseSchedulerNode], dict[BaseSchedulerNode, ReorderInfo]]:
    """
    Internal testing helper that also returns debug info.
    Returns:
        - reordered snodes list
        - dict {snode: ReorderInfo}
    """
    has_collectives = False
    for snode in snodes:
        if contains_collective(snode):
            has_collectives = True
            break
    if not has_collectives:
        return snodes, {}

    original_snodes_num = len(snodes)
    # heuristic to avoid degenerating to quadratic time
    graph_inputs: OrderedSet[str] = OrderedSet(V.graph.graph_inputs.keys())
    graph_outputs: OrderedSet[str] = OrderedSet(V.graph.get_output_names())
    (
        peak_memory,
        _curr_memory,
        snodes_allocfree,
        buf_to_snode_last_use,
        name_to_freeable_input_buf,
        candidate_buffer_map,
    ) = _initialize_memory_tracking(snodes, graph_inputs, graph_outputs)

    runtimes: dict[BaseSchedulerNode, float] = {
        snode: estimate_op_runtime(snode) * _op_runtime_estimate_mult(snode)
        for snode in snodes
    }

    # Pre-compute output and dependency sets for O(1) lookup instead of O(N) creation per iteration
    node_output_sets: dict[BaseSchedulerNode, frozenset[str]] = {
        snode: frozenset(o.get_name() for o in snode.get_outputs()) for snode in snodes
    }
    node_dep_sets: dict[BaseSchedulerNode, frozenset[str]] = {
        snode: frozenset(
            d.name for d in snode.unmet_dependencies if not _is_fake_dep(d)
        )
        for snode in snodes
    }

    # debug stats
    stats: dict[BaseSchedulerNode, ReorderInfo] = {}

    total_moves = 0

    _prev, _next, _head = _initialize_double_linked_list(snodes)

    debug_num_collectives_to_reorder: int | None = (
        config_comms.reorder_iterative_debug_limit_to_reorder
    )

    num_processed_collectives: int = 0
    curr: BaseSchedulerNode | None = _head
    debug_iterative_memory_recompute = (
        config_comms.reorder_iterative_debug_memory_recompute
    )
    iterative_recompute_error = False

    while curr is not None and _next[curr] is not None:
        _next_curr = _next[curr]
        if iterative_recompute_error:
            break

        if not contains_async_collective(curr):
            curr = _next_curr
            continue

        if debug_num_collectives_to_reorder is not None and (
            num_processed_collectives >= debug_num_collectives_to_reorder
        ):
            break
        num_processed_collectives += 1

        info = stats[curr] = ReorderInfo()
        comm_time, comp_time, overlap_info = _coll_exposed_communication_time(
            curr, _next, runtimes, node_output_sets, node_dep_sets
        )
        info.comm_time = comm_time
        info.comp_time = comp_time
        info.initial_exposed = info.final_exposed = comm_time - comp_time
        info.overlap_info = overlap_info

        candidate = _prev[curr]
        group_head = curr
        group_tail = curr
        group_waits = {}
        group_runtime = 0.0
        group_peak_memory = _curr_memory[curr][0]  # post_alloc memory

        # Track group dependencies incrementally - initialize from pre-computed sets
        group_unmet_deps_names = OrderedSet(node_dep_sets[curr])
        group_output_names = OrderedSet(node_output_sets[curr])

        while candidate is not None:
            if config_comms.reorder_iterative_use_runtime_estimations and (
                info.final_exposed
                < -config_comms.reorder_iterative_extra_comm_comp_overlap
                * info.comm_time
            ):
                info.limiting_factor = "unexposed by runtime estimations"
                break

            if (
                not config_comms.reorder_iterative_unsafe_collectives_reorder
                and contains_collective(candidate)
            ):
                info.limiting_factor = "collective ordering"
                break

            # Early exit: if group has no unmet dependencies, candidate can't have data dependency
            data_deps_names = group_unmet_deps_names - group_output_names
            if not data_deps_names:
                data_dep = False
            else:
                # Calculate effective dependencies (not satisfied within group)
                # Use pre-computed set for O(1) lookup
                candidate_out_names = node_output_sets[candidate]
                data_dep = bool(candidate_out_names & data_deps_names)

            if data_dep:
                is_groupable_result, grouping_reason = _is_node_groupable_for_reorder(
                    candidate
                )
                if is_groupable_result:
                    group_head = candidate

                    # Update incremental dependency tracking using pre-computed sets
                    group_unmet_deps_names.update(node_dep_sets[candidate])
                    group_output_names.update(node_output_sets[candidate])

                    if config_comms.reorder_iterative_use_runtime_estimations:
                        if contains_wait(candidate):
                            comm_time, comp_time, _ = _wait_exposed_communication_time(
                                candidate,
                                _head,
                                _prev,
                                runtimes,
                                node_output_sets,
                                node_dep_sets,
                            )
                            group_waits[candidate] = comm_time, comp_time
                        if not contains_async_collective(candidate):
                            group_runtime += runtimes[candidate]

                    group_peak_memory = max(
                        group_peak_memory, _curr_memory[candidate][0]
                    )
                    info.grouped += 1
                    candidate = _prev[candidate]
                    continue
                else:
                    msg = (
                        f"data dependency detected"
                        f"\n candidate:{candidate.get_name()}(outs:{[o.get_name() for o in candidate.get_outputs()]})"
                        f"\n non_group_reason:{grouping_reason}"
                    )
                    info.limiting_factor = msg
                    break

            if config_comms.reorder_iterative_use_runtime_estimations:
                # Check if candidate has sync runtime
                if not contains_async_collective(candidate):
                    c_runtime = runtimes[candidate]

                    if c_runtime > 0 and len(group_waits) > 0:
                        # pyrefly: ignore[no-matching-overload]
                        exposed_before = max(0, info.comm_time - info.comp_time)
                        # pyrefly: ignore[no-matching-overload]
                        exposed_after = max(
                            0, info.comm_time - info.comp_time - c_runtime
                        )
                        exposed_delta = exposed_after - exposed_before
                        for gw_comm_time, gw_comp_time in group_waits.values():
                            # pyrefly: ignore [no-matching-overload]
                            gw_exposed_before = max(0, gw_comm_time - gw_comp_time)
                            # pyrefly: ignore [no-matching-overload]
                            gw_exposed_after = max(
                                0, gw_comm_time - gw_comp_time + c_runtime
                            )

                            exposed_delta += gw_exposed_after - gw_exposed_before

                        if exposed_delta > 0:
                            info.limiting_factor = (
                                f"candidate has compute {c_runtime},"
                                f" group contains waits, total_exposed_delta {exposed_delta}"
                            )
                            break
                        else:
                            # Update all group_colls comm_time, comp_time
                            for gw, (
                                gw_comm_time,
                                gw_comp_time,
                            ) in group_waits.items():
                                group_waits[gw] = (
                                    gw_comm_time,
                                    gw_comp_time - c_runtime,
                                )
                else:
                    # Candidate is async_collective

                    # Unsafe collectives reordering
                    # Cj -> [...group_runtime..., Ci] -> Wj
                    # Checking that we are not increasing exposed time of Cj
                    if group_runtime > 0:
                        comm_time, comp_time, _ = _coll_exposed_communication_time(
                            candidate, _next, runtimes, node_output_sets, node_dep_sets
                        )
                        # pyrefly: ignore[no-matching-overload]
                        exposed_before = max(0, comm_time - comp_time)
                        # pyrefly: ignore[no-matching-overload]
                        exposed_after = max(0, comm_time - comp_time + group_runtime)
                        exposed_delta = exposed_after - exposed_before
                        if exposed_delta > 0:
                            info.limiting_factor = (
                                f"candidate {candidate.get_name()} is collective,"
                                f" group_runtime:{group_runtime},"
                                f" exposed_delta:{exposed_delta} c_comm_time:{comm_time} c_comp_time:{comp_time}"
                            )
                            break

            # Create group nodes list once for swap operations
            gns: list[BaseSchedulerNode] = _group_nodes_from_linked_list(
                group_head, group_tail, _next
            )

            candidate_allocfree: SNodeMemory = snodes_allocfree[candidate]
            candidate_delta_mem: int = (
                candidate_allocfree.size_alloc - candidate_allocfree.size_free
            )
            # candidate and one of group nodes are successors of the same buffer
            # and last use of the buffer happen in group nodes.
            # This last use deallocates it.
            # If we swap [candidate [group]] to [[group] candidate],
            # candidate becomes the last use
            # and deallocated this buffer instead of group node.
            # we need to update size_free accordingly to group_node and candidate,
            # and recalculate post_alloc, post_free for them.
            #
            # Buf that changes its last use snode,
            # after swap will be deallocated only by candidate,
            # while before it was deallocated by group node.
            group_n_to_bufs_after_swap_dealloc_by_candidate = (
                _find_buffers_with_changed_last_use(
                    candidate, gns, buf_to_snode_last_use, candidate_buffer_map
                )
            )

            potential_peak, _post_alloc_update = (
                _calculate_potential_peak_memory_reorder(
                    candidate,
                    gns,
                    group_tail,
                    group_peak_memory,
                    candidate_delta_mem,
                    candidate_allocfree,
                    group_n_to_bufs_after_swap_dealloc_by_candidate,
                    _curr_memory,
                )
            )

            if (
                potential_peak - peak_memory
                > peak_memory * config_comms.reorder_iterative_peak_memory_budget
            ):
                info.limiting_factor = (
                    f"peak memory new:{potential_peak} vs base:{peak_memory}"
                )
                break
            info.moves += 1
            total_moves += 1

            _head = _perform_double_linked_list_swap(
                candidate, group_head, group_tail, _prev, _next, _head
            )

            comm_time, comp_time, overlap_info = _coll_exposed_communication_time(
                curr, _next, runtimes, node_output_sets, node_dep_sets
            )
            info.comm_time = comm_time
            info.comp_time = comp_time
            info.overlap_info = overlap_info
            info.final_exposed = comm_time - comp_time

            _update_memory_tracking_after_swap_reorder(
                candidate,
                gns,
                group_tail,
                candidate_delta_mem,
                candidate_allocfree,
                group_n_to_bufs_after_swap_dealloc_by_candidate,
                _post_alloc_update,
                _curr_memory,
                buf_to_snode_last_use,
                snodes_allocfree,
            )

            if debug_iterative_memory_recompute:
                # Compare iteratively recomputed memory data
                # with full run of estimate_peak_memory

                from .comms_debug import _debug_iterative_memory_recompute

                iterative_recompute_error = _debug_iterative_memory_recompute(
                    candidate,
                    gns,
                    _group_names(gns),
                    _group_nodes_from_linked_list(_head, None, _next),
                    name_to_freeable_input_buf,
                    graph_outputs,
                    peak_memory,
                    _curr_memory,
                    snodes_allocfree,
                    "reorder_communication_preserving_peak_memory",
                    group_n_to_bufs_after_swap_dealloc_by_candidate,
                )
                if iterative_recompute_error:
                    break
            candidate = _prev[group_head]
        curr = _next_curr

    if not config_comms.reorder_sink_verbose_logging:
        new_snodes = _group_nodes_from_linked_list(_head, None, _next)
        return new_snodes, stats

    new_snodes = _format_and_log_reordering_stats(
        stats,
        _head,
        _next,
        original_snodes_num,
        peak_memory,
        name_to_freeable_input_buf,
        graph_outputs,
    )

    return new_snodes, stats