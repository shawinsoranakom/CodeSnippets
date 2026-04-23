def _sync(autotune_results: list[_SerializedChoice]) -> Sequence[_SerializedChoice]:
    """
    Perform the all_gather to collect the autotune results from all the ranks.
    """

    autotune_pg = get_autotune_pg()
    assert autotune_pg

    # Perform allgather
    all_states: list[list[_SerializedChoice]] = [None] * autotune_pg.size()  # type: ignore[list-item]
    torch.distributed.all_gather_object(all_states, autotune_results, group=autotune_pg)

    node_count = sum(len(x) for x in all_states)
    # It's faster to briefly lie about the type than to unzip the results and append.
    choices_by_index: list[_SerializedChoice] = [None] * node_count  # type: ignore[list-item]

    check_count = 0
    for other_results in all_states:
        for choice in other_results:
            assert isinstance(choice, _SerializedChoice)
            assert choices_by_index[choice.index] is None
            choices_by_index[choice.index] = choice
            check_count += 1

    assert node_count == check_count, f"count mismatch: {node_count} != {check_count}"
    return choices_by_index