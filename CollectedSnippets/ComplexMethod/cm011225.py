def match_coalesced_groups(
    all_rank_events: dict[Any, Any],
    group_size: int,
    groups: dict[str, Group],
    memberships: dict[str, set[Any]],
    _pg_guids: dict[tuple[str, int], str],
) -> bool:
    """
    all_rank_events: {
        rank: [
            (idx, event_dict)
        ]
    }

    Note: it is possible for event dicts in a coalesced group to be asymmetric.
        e.g. the following events lists form a valid coalescing group
             events0 [send:1]
             events1 [recv:0, send:2]
             events2 [recv:1]

    Rule 1: all ops should find a match
    Rule 2: relative ordering of sends and recvs in one event list can be arbitrary
        e.g.
        events1 [recv:0, send:2]  —> okay
        events1 [send:2, recv:0] —> also okay
    Rule 3: sends to the same dest or recvs from the src should be in a consistent order
        e.g.
        rank0 [send:1 (100B), send:1 (1000B)]
        rank1 [recv:0 (1000B), recv:0 (100B)]   —> not okay
    """
    all_ops = {
        rank: [
            Op(e, memberships, _pg_guids[(e["process_group"][0], rank)])
            for i, e in all_rank_events[rank]
        ]
        for rank in all_rank_events
    }

    def visualize_ops(
        match: bool,
        _pg_guids: dict[tuple[str, int], str],
    ) -> None:
        all_ops = {
            rank: [
                Op(e, memberships, _pg_guids[(e["process_group"][0], rank)])
                for i, e in all_rank_events[rank]
            ]
            for rank in all_rank_events
        }

        i = 0
        row = []
        progress = True
        table = []
        while progress:
            progress = False
            for r in all_ops:
                if len(all_ops[r]) > i:
                    rank, event = all_rank_events[r][i]
                    # Check if the pg_guid exists for this rank and process group
                    pg_key = (event["process_group"][0], rank)
                    if pg_key in _pg_guids:
                        row.append(
                            Op(
                                event,
                                memberships,
                                _pg_guids[pg_key],
                            )
                        )
                    else:
                        # Skip this entry if pg_guid mapping doesn't exist
                        row.append(None)  # type: ignore[arg-type]
                    progress = True
                else:
                    row.append(None)  # type: ignore[arg-type]
            table.append(row)
            row = []
            i += 1
        title = "Match" if match else "MISMATCH"
        logger.info("%s \n", title)
        logger.info("%s", tabulate(table))  # type: ignore[operator]

    # TODO can't verify seq_id bc there might have been valid seq deltas between ranks even within a pg.
    for op_list in all_ops.values():
        if not op_list:
            # print("TODO- not sure if its valid for only some ranks in a PG to participate in a coalesced op?")
            return False
        if op_list[-1].type != "coalesced":
            raise AssertionError
        op_list.pop(-1)

    while all_ops:
        first_rank = next(iter(all_ops))
        my_ops = all_ops[first_rank]

        if len(all_ops[first_rank]) == 0:
            all_ops.pop(first_rank)
            continue

        # lets match the first collective! we need to know which ranks are involved, and ensure that this same
        # collective is also the first one on those ranks within that group
        op = my_ops[0]
        match_idx = -1
        if op.type in P2P:
            dst_global_rank = sorted(memberships[op.pg_name])[op.dst]
            peer_ops = all_ops[dst_global_rank]
            for i, other in enumerate(peer_ops):
                if op.match(other).state == MatchState.FULLY_MATCHED:
                    match_idx = i
                    break
                elif op.dst == other.src:
                    # Rule 3
                    break
                else:
                    # Rule 1
                    continue
        else:
            raise NotImplementedError("coalesced collective ops")
        if match_idx >= 0:
            my_ops.pop(0)
            peer_ops.pop(match_idx)
        else:
            visualize_ops(False, _pg_guids)
            return False

    visualize_ops(True, _pg_guids)
    return True