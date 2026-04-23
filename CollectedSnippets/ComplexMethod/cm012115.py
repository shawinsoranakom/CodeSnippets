def _sink_waits_iterative_internal(
    snodes: list[BaseSchedulerNode],
) -> tuple[list[BaseSchedulerNode], dict[BaseSchedulerNode, SinkWaitInfo]]:
    original_snodes_num = len(snodes)
    if original_snodes_num == 0:
        return snodes, {}
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

    _prev, _next, _head = _initialize_double_linked_list(snodes)

    stats: dict[BaseSchedulerNode, SinkWaitInfo] = {}

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

    curr: BaseSchedulerNode | None = snodes[-1]

    processed_waits = OrderedSet()  # type: ignore[var-annotated]
    debug_iterative_memory_recompute = (
        config_comms.reorder_iterative_debug_memory_recompute
    )
    debug_num_sink_waits_to_reorder: int | None = (
        config_comms.sink_waits_iterative_debug_limit_to_sink
    )

    iterative_recompute_error = False
    while curr is not None and _prev[curr] is not None:
        _prev_curr = _prev[curr]
        if iterative_recompute_error:
            break
        if (
            debug_num_sink_waits_to_reorder is not None
            and len(processed_waits) >= debug_num_sink_waits_to_reorder
        ):
            break

        if not (contains_wait(curr) and curr not in processed_waits):
            curr = _prev_curr
            continue

        processed_waits.add(curr)
        info = stats[curr] = SinkWaitInfo()
        comm_time, comp_time, overlap_info = _wait_exposed_communication_time(
            curr, _head, _prev, runtimes, node_output_sets, node_dep_sets
        )
        info.initial_exposed = info.final_exposed = comm_time - comp_time
        info.comm_time = comm_time
        info.comp_time = comp_time
        info.overlap_info = overlap_info

        candidate = _next[curr]
        group_head = curr
        group_tail = curr
        group_colls = {}
        group_runtime = 0.0
        group_peak_memory = _curr_memory[curr][0]

        # Track group outputs and check collective status incrementally - initialize from pre-computed set
        group_output_names = OrderedSet(node_output_sets[curr])
        group_contains_collective = contains_collective(curr)

        while candidate is not None:
            if config_comms.sink_iterative_use_runtime_estimations and (
                info.final_exposed
                < -config_comms.sink_iterative_extra_comm_comp_overlap * info.comm_time
            ):
                info.limiting_factor = "unexposed by runtime estimations"
                break

            # Early exit: if group has no outputs, candidate can't depend on it
            if not group_output_names:
                data_dep = False
            else:
                # Calculate candidate dependencies using pre-computed set
                candidate_dep_names = node_dep_sets[candidate]
                data_dep = bool(candidate_dep_names & group_output_names)

            # Conservative sink wait, limiting by space before next collective.
            # The global strategy is that bucketing should create space.
            # For 2D we can experiment with allowing to sink Wait beyond non current group collective.

            if not config_comms.sink_waits_iterative_swap_with_collectives:
                if contains_async_collective(candidate):
                    info.limiting_factor = (
                        f"candidate contains_async_collective {candidate.get_name()}"
                    )
                    break

            # 1. If we have data_dep - we can not swap => trying to group
            # 2. If swap candidate and current node both contain collectives => trying to group
            both_contain_comms = group_contains_collective and contains_collective(
                candidate
            )
            if data_dep or both_contain_comms:
                _is_groupable, groupable_reason = _is_node_groupable_for_sink_waits(
                    candidate
                )
                if _is_groupable:
                    group_tail = candidate

                    # Update incremental tracking using pre-computed set
                    group_output_names.update(node_output_sets[candidate])
                    group_contains_collective = (
                        group_contains_collective or contains_collective(candidate)
                    )

                    if (
                        config_comms.sink_iterative_use_runtime_estimations
                        and contains_collective(candidate)
                    ):
                        comm_time, comp_time, _ = _coll_exposed_communication_time(
                            candidate, _next, runtimes, node_output_sets, node_dep_sets
                        )
                        group_colls[candidate] = (comm_time, comp_time)
                        if not contains_async_collective(candidate):
                            group_runtime += runtimes[candidate]

                    group_peak_memory = max(
                        group_peak_memory, _curr_memory[candidate][0]
                    )
                    info.grouped += 1
                    candidate = _next[candidate]
                    continue
                elif not data_dep:
                    if (
                        not config_comms.sink_waits_iterative_unsafe_collectives_reorder
                        and both_contain_comms
                    ):
                        info.limiting_factor = (
                            f"collective ordering"
                            f"\n with candidate:{candidate.get_name()}"
                        )
                        break
                else:
                    info.limiting_factor = (
                        f"data dependency detected"
                        f"\n candidate:{candidate.get_name()}"
                        f"\n non_group_reason:{groupable_reason}"
                    )
                    break

            if config_comms.sink_iterative_use_runtime_estimations:
                if is_wait(candidate.node):
                    # Corresponding collective is before the group,
                    # Swap can increase exposed time of corresponding collective
                    comm_time, comp_time, _ = _wait_exposed_communication_time(
                        candidate,
                        _head,
                        _prev,
                        runtimes,
                        node_output_sets,
                        node_dep_sets,
                    )
                    # pyrefly: ignore[no-matching-overload]
                    exposed_before = max(0, comm_time - comp_time)
                    # pyrefly: ignore[no-matching-overload]
                    exposed_after = max(0, comm_time - comp_time + group_runtime)
                    # We do not know how much we can sink more after this swap,
                    # Just comparing advantage at the moment for now.
                    if exposed_after > exposed_before:
                        info.limiting_factor = (
                            "candidate is wait,"
                            f" exposed_before:{exposed_before} vs exposed_after:{exposed_after}"
                        )
                        break

                # Check if candidate has sync runtime
                if not contains_async_collective(candidate):
                    # If candidate has sync runtime,
                    # Waits of gorup_colls are on the right from group.
                    # Swap can increase their exposed time.
                    c_runtime = runtimes[candidate]

                    if c_runtime > 0 and len(group_colls) > 0:
                        # Advantage for current Wait to do the Swap
                        # pyrefly: ignore[no-matching-overload]
                        exposed_delta = max(
                            0,
                            info.comm_time - info.comp_time,
                        )
                        # pyrefly: ignore[no-matching-overload]
                        -max(0, info.comm_time - info.comp_time - c_runtime)
                        for gc_comm_time, gc_comp_time in group_colls.values():
                            # pyrefly: ignore [no-matching-overload]
                            exposed_delta += max(0, gc_comm_time - gc_comp_time) - max(
                                0, gc_comm_time - gc_comp_time + c_runtime
                            )
                        if exposed_delta > 0:
                            info.limiting_factor = (
                                f"candidate has compute {c_runtime}, group contains collectives,"
                                f" total_exposed_delta {exposed_delta}"
                            )
                            break
                        else:
                            # Update all group_colls comm_time, comp_time
                            for gc, (
                                gc_comm_time,
                                gc_comp_time,
                            ) in group_colls.items():
                                group_colls[gc] = (
                                    gc_comm_time,
                                    gc_comp_time - c_runtime,
                                )

            # Create group nodes list once for swap operations
            gns: list[BaseSchedulerNode] = _group_nodes_from_linked_list(
                group_head, group_tail, _next
            )

            candidate_allocfree: SNodeMemory = snodes_allocfree[candidate]
            candidate_delta_mem = (
                candidate_allocfree.size_alloc - candidate_allocfree.size_free
            )
            # [group] candidate -> candidate [group]
            # Check for buffers with successors in group and candidate last successor
            #
            # Buf that  changes its last use snode,
            # It was deallocated by candidate,
            # but after swap it will be deallocated by group node.
            group_n_to_bufs_after_swap_dealloc_instead_of_candidate = (
                _find_buffers_with_changed_last_use_sink_waits(
                    candidate, gns, buf_to_snode_last_use, candidate_buffer_map
                )
            )

            potential_peak, _post_alloc_update, _size_free_delta_update = (
                _calculate_potential_peak_memory_sink_waits(
                    candidate,
                    gns,
                    group_head,
                    group_peak_memory,
                    candidate_delta_mem,
                    candidate_allocfree,
                    group_n_to_bufs_after_swap_dealloc_instead_of_candidate,
                    _curr_memory,
                    snodes_allocfree,
                )
            )
            if (
                potential_peak - peak_memory
                > peak_memory * config_comms.sink_iterative_peak_memory_budget
            ):
                info.limiting_factor = (
                    f"peak memory new:{potential_peak} vs base:{peak_memory}"
                )
                break

            info.moves += 1
            info.moves_info += f"+{candidate.get_name()}"

            _head = _perform_double_linked_list_swap_sink_waits(
                candidate, group_head, group_tail, _prev, _next, _head
            )

            comm_time, comp_time, overlap_info = _wait_exposed_communication_time(
                curr, _head, _prev, runtimes, node_output_sets, node_dep_sets
            )
            info.comm_time = comm_time
            info.comp_time = comp_time
            info.final_exposed = comm_time - comp_time
            info.overlap_info = overlap_info

            _update_memory_tracking_after_swap_sink_waits(
                candidate,
                gns,
                candidate_delta_mem,
                candidate_allocfree,
                group_n_to_bufs_after_swap_dealloc_instead_of_candidate,
                _post_alloc_update,
                _size_free_delta_update,
                _curr_memory,
                snodes_allocfree,
            )

            if debug_iterative_memory_recompute:
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
                    "sink_waits_iterative",
                    group_n_to_bufs_after_swap_dealloc_instead_of_candidate,
                )
                if iterative_recompute_error:
                    break

            candidate = _next[group_tail]
        curr = _prev_curr

    if not config_comms.reorder_sink_verbose_logging:
        new_snodes = _group_nodes_from_linked_list(_head, None, _next)
        return new_snodes, stats

    new_snodes = _format_and_log_sink_waits_stats(
        stats,
        _head,
        _next,
        original_snodes_num,
        peak_memory,
        name_to_freeable_input_buf,
        graph_outputs,
    )

    return new_snodes, stats