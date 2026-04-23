def _autotune_local_nodes(
    scheduler: torch._inductor.scheduler.Scheduler,
) -> list[_SerializedChoice]:
    """
    Go through the nodes in the scheduler and autotune the kernels which
    should be autotuned by this rank.
    """

    autotune_results: list[_SerializedChoice] = []

    for node in scheduler.nodes:
        if not isinstance(node, SchedulerNode):
            continue

        if (inner_node := node.node) is None:
            continue

        if isinstance(inner_node, _DistributedAutotuneBuffer):
            # This is marked for remote autotuning.
            continue

        if not isinstance(inner_node, MultiTemplateBuffer):
            continue

        if (origin_node := inner_node.origin_node) is None:
            continue

        if (meta := origin_node.meta) is None:
            continue

        info = meta.get(_DISTRIBUTED_AUTOTUNE_KEY)
        if info is None:
            continue

        assert info.local

        # We force autotuning here
        # Still takes advantage of async precompile
        # We need all the configs before fusion
        min_choice, _ = inner_node.get_min_choice()

        choice = _SerializedChoice(info.index, min_choice)
        autotune_results.append(choice)

    state = V.distributed_autotune_state
    assert len(autotune_results) == state.autotuned_local_count, (
        f"incorrect local autotuned nodes found ({len(autotune_results)} != {state.autotuned_local_count})"
    )
    return autotune_results