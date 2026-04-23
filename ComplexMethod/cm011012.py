def _find_or_create_pg_by_ranks_and_tag(
    tag: str, ranks: list[int], stride: int
) -> ProcessGroup:
    if len(ranks) % stride != 0:
        raise ValueError(
            f"Ranks length ({len(ranks)}) must be divisible by stride ({stride})"
        )

    my_rank = get_rank()
    my_ranks = None

    if stride == len(ranks):
        my_ranks = ranks.copy()
        if my_rank not in my_ranks:
            raise AssertionError("rankset doesn't include the current node")
    else:
        for i in range(0, len(ranks), stride):
            rank_set = ranks[i : i + stride]
            if my_rank in rank_set:
                my_ranks = rank_set
        if my_ranks is None:
            raise AssertionError("rankset doesn't include the current node")

    my_ranks = sorted(my_ranks)

    pg = _find_pg_by_ranks_and_tag(tag, my_ranks)
    if pg is not None:
        return pg
    if tag == "":
        raise ValueError("Cannot automatically create PG with empty tag")
    # TODO copy settings and timeout from default PG
    return _new_group_with_tag(my_ranks, pg_tag=tag)