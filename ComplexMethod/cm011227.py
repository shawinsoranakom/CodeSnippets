def check_current_entry_match(
    all_entries: dict[int, list[dict[str, Any]]],
    _pg_guids: dict[tuple[str, int], str],
    pg_info: tuple[str, str],
    current_entry: dict[str, Any],
    _memberships: dict[str, set[Any]],
    mismatch: dict[str, int],
    match_record: MatchStateRecord,
) -> None:
    pg_name, desc = pg_info[0], pg_info[1]
    for o in match_record.expected_ranks.intersection(set(match_record.other_ranks)):
        for i, e in enumerate(all_entries[o]):  # type: ignore[index]
            # step over ops from other PGs
            # only check match state when seq_id matches
            if (
                _pg_guids[(e["process_group"][0], o)] == pg_name
                and e["process_group"][1] == desc
                and e["collective_seq_id"] == match_record.entry_state.collective_seq_id
            ):
                match_info = match_one_event(current_entry, e, _memberships, pg_name)
                if (
                    match_info.state in [MatchState.FULLY_MATCHED, MatchState.UNDECIDED]
                    and mismatch[pg_name] == 0
                ):
                    match_record.found_ranks.add(o)
                    match_record.found_idx[o] = i
                    match_record.has_undecided_case = (
                        match_info.state == MatchState.UNDECIDED
                    )
                else:
                    match_record.candidate_ranks.add(o)
                    match_record.candidate_idx[o] = i
                    if match_info.state not in [
                        MatchState.FULLY_MATCHED,
                        MatchState.UNDECIDED,
                    ]:
                        # Here we assume the current rank is not the source of the error.
                        # But it's possible that the current rank is the culprit, then users will
                        # see lots of normal ranks reported as culprit.
                        # TODO: we need to figure out a better way to handle the case mentioned above.
                        match_record.errors.add((o, match_info))
                break