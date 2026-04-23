def build_collectives(
    all_entries: dict[int, list[dict[str, Any]]],
    _groups: dict[str, Group],
    _memberships: dict[str, set[Any]],
    _pg_guids: dict[tuple[str, int], str],
    version: str,
    mismatch_cap: int = 10,
) -> tuple[list[Traceback], list[Collective], list[NCCLCall]]:
    """
    groups, memberships are the non-flat dicts that are indexable
    all_entries is a raw dict from the original dumps:

    all_entries: {
        global_rank: [
            {
                record_id: ordered id of the event in the trace buffer
                pg_id: ProcessGroupNCCL::uid_
                    *note: `pg_id` corresponds to nothing in groups table
                process_group: (pg_name, desc)
                    *note: `pg_name`, `desc` corresponds to `pg_id`, `desc` in groups table
                collective_seq_id: ordered id for collective operations and coalesced group operations
                p2p_seq_id: ordered id for point-to-point operations
                op_id: ordered id including individual ops inside coalescing group
                profiling_name: descriptive name of the operation
                'time_created_ns',
                'input_sizes',
                'output_sizes',
                'state',
                'time_discovered_started_ns',
                'time_discovered_completed_ns',
                'retired',
                'frames',
            }
        ]
    }
    """
    tracebacks: list[Traceback] = []

    collectives: list[Collective] = []
    nccl_calls: list[NCCLCall] = []

    # once we find one mismatch, we stop pairing up collectives since the pairing is possibly incorrect
    # instead, just record the remaining ops as NCCLCalls
    mismatch = {_groups[g].id: 0 for g in _groups}

    # For best effort partial analysis.
    dumps_ranks = {int(key) for key in all_entries}
    """
    - it doesn't matter what order I put collectives/ncclops into their table. we can later on re-sort it by start time
    - there could be multiple options for the "first" collective to pair up (rank 0,1 might do a bcast while rank 2,3 do a bcast)
    - within a group, the first collective must be the same on all ranks in the group, then it can be marked as a
    collective and removed
    """
    while all_entries:
        # we greedily match collectives, starting arbitrarily with the trace from the first rank
        # later, if we exhaust the first rank, we continue with the next 'first rank'
        rank_iter = iter(all_entries)
        first_rank = next(rank_iter)
        other_ranks = list(rank_iter)

        if len(all_entries[first_rank]) == 0:
            all_entries.pop(first_rank)
            continue

        # lets match the first collective! we need to know which ranks are involved, and ensure that this same
        # collective is also the first one on those ranks within that group
        entries = all_entries[first_rank]
        current_entry = entries[0]
        desc = current_entry["process_group"][1]
        # For db build and logs printing, we want to use the original pg_name, not the hash one.
        original_pg_name = current_entry["process_group"][0]
        pg_name = _pg_guids[(original_pg_name, first_rank)]
        expected_ranks = set(_memberships[pg_name])
        entry_state = EntryState(current_entry, expected_ranks)
        match_record = MatchStateRecord(
            expected_ranks=expected_ranks,
            other_ranks=other_ranks,
            entry_state=entry_state,
            candidate_ranks={first_rank},
            candidate_idx={},
            found_ranks=set(),
            found_idx={},
            errors=set(),
        )

        major_v, minor_v = get_version_detail(version)
        find_coalesced_group = (
            find_coalesced_group_p2p_only
            if major_v <= 2 and minor_v < 7
            else find_coalesced_group_with_non_p2p
        )
        maybe_coalesced_group = find_coalesced_group(
            pg_name, entries, _pg_guids, first_rank
        )
        if len(maybe_coalesced_group) > 1:
            num_coalesced_entries = len(maybe_coalesced_group)
            # We need a copy of the original expected ranks to avoid modifying it.
            candidate_ranks = copy.deepcopy(expected_ranks)
            done_ranks = set()
            all_coalesced_entries = {}
            while candidate_ranks:
                curr = candidate_ranks.pop()
                done_ranks.add(curr)
                grp = (
                    find_coalesced_group(pg_name, all_entries[curr], _pg_guids, curr)  # type: ignore[index]
                    if curr in all_entries  # type: ignore[comparison-overlap]
                    else []
                )
                all_coalesced_entries[curr] = grp
                for _, entry in grp:
                    op = Op(entry, _memberships, pg_name)
                    peer = None
                    if op.type == "send":
                        if op._src_g != curr:
                            raise AssertionError(
                                f"Send src error: {curr} expected but {op._src_g} is set"
                            )
                        peer = op._dst_g
                    elif op.type == "recv":
                        if op._dst_g != curr:
                            raise AssertionError(
                                f"Recv dst error: {curr} expected but {op._dst_g} is set"
                            )
                        peer = op._src_g
                    if peer and peer not in done_ranks:
                        candidate_ranks.add(peer)

            if major_v <= 2 and minor_v < 7:
                match = match_coalesced_groups_p2p_only(
                    all_coalesced_entries,
                    group_size=_groups[pg_name].size,
                    groups=_groups,
                    memberships=_memberships,
                    _pg_guids=_pg_guids,
                )
            else:
                match = match_coalesced_groups_with_non_p2p(
                    copy.deepcopy(
                        all_coalesced_entries
                    ),  # We want to keep a copy for cleanup.
                    pg_info=(pg_name, desc),
                    memberships=_memberships,
                    _pg_guids=_pg_guids,
                    mismatch=mismatch,
                    dumps_ranks=dumps_ranks,
                    version=version,
                    collectives=collectives,
                    match_record=match_record,
                )

            if match and mismatch[pg_name] == 0:
                # We treat coalesced collectives as a single collective.
                # TODO: we need to surface a merged collective info like input/output sizes to users.
                collectives.append(
                    match_record.entry_state.to_collective(len(collectives))
                )
            else:
                mismatch[pg_name] += 1
            for r in all_coalesced_entries:
                idx_map = {r: i for i, _ in reversed(all_coalesced_entries[r])}  # noqa: B035
                nccl_calls.extend(
                    reversed(
                        match_record.entry_state.to_nccl_call(
                            all_entries,
                            idx_map,
                            len(nccl_calls),
                            collectives[-1].id if match else None,
                        )
                    )
                )
                # This extra cleanup is needed because we need to pop all collectives within a coalesced collective.
                for i, k in idx_map.items():
                    for _ in range(1, num_coalesced_entries):
                        try:
                            all_entries[i].pop(k)
                        except IndexError:
                            # In the case of a missing rank symptom that a rank didn't schedule the coalesced collective,
                            # we should not fail the analysis script here.
                            pass
        else:
            # Iterate through all the ranks and check if there is a mismatch for the current entry.
            check_current_entry_match(
                all_entries,
                _pg_guids,
                (pg_name, desc),
                current_entry,
                _memberships,
                mismatch,
                match_record,
            )

            # Use heuristics to decide what type of errors and error messages we should print.
            error_analysis(
                all_entries,
                match_record,
                dumps_ranks,
                first_rank,
                current_entry,
                mismatch,
                get_version_detail(version),
                pg_name,
            )

            # at this point there are 3 possibilities
            # 1. we found a match on all the ranks that are members of the group
            #  -> we create a Collective and remove the individual entries from their original lists
            if match_record.found_ranks == expected_ranks and mismatch[pg_name] == 0:
                collectives.append(
                    match_record.entry_state.to_collective(len(collectives))
                )
                idx_map = {
                    r: match_record.found_idx[r] if r != first_rank else 0
                    for r in match_record.found_ranks
                }
                nccl_calls.extend(
                    match_record.entry_state.to_nccl_call(
                        all_entries, idx_map, len(nccl_calls), collectives[-1].id
                    )
                )

            # 2. we found a partial match but some ranks are missing
            # 3. we found no match
            #  -> since its not a complete collective, no entry goes into collectives but we still record a nccl call
            #     TODO should there be a way to mark 'mismatches'?
            else:
                logger.debug("appending a non-matching collective")
                idx_map = {
                    r: match_record.candidate_idx[r] if r != first_rank else 0
                    for r in match_record.candidate_ranks
                }
                collectives.append(
                    match_record.entry_state.to_collective(
                        len(collectives),
                        errors=match_record.errors,
                        idx_map=idx_map,
                        all_entries=all_entries,
                    )
                )
                nccl_calls.extend(
                    match_record.entry_state.to_nccl_call(
                        all_entries, idx_map, len(nccl_calls), None
                    )
                )

        if mismatch[pg_name] > mismatch_cap:
            logger.error(
                "Too many mismatches for process_group %s: %s aborting", pg_name, desc
            )
            break

    return tracebacks, collectives, nccl_calls