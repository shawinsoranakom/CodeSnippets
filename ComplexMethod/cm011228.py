def error_analysis(
    all_entries: dict[int, list[dict[str, Any]]],
    match_record: MatchStateRecord,
    dumps_ranks: set[int],
    first_rank: int,
    current_entry: dict[str, Any],
    mismatch: dict[str, int],
    version: tuple[int, int],
    pg_name: str,
) -> None:
    major_v, minor_v = version[0], version[1]
    # case one: not every rank join the collective or in the flight recorder.
    if (
        match_record.candidate_ranks | match_record.found_ranks
    ) != match_record.expected_ranks and match_record.expected_ranks - (
        match_record.candidate_ranks | match_record.found_ranks
    ) <= dumps_ranks:
        mismatch[pg_name] += 1
        logger_msg = "Not all ranks joining collective, sequence number: %s"
        missing_ranks = match_record.expected_ranks - (
            match_record.candidate_ranks | match_record.found_ranks
        )
        match_record.entry_state.log(
            logger, logger_msg, format_frames, missing_ranks=missing_ranks
        )
        match_record.candidate_ranks.update(match_record.found_ranks)
        match_record.candidate_idx.update(match_record.found_idx)
        match_record.found_idx.clear()
        match_record.found_ranks.clear()
    # We didn't see any mismatch and all expected ranks are in the dump.
    elif len(
        match_record.candidate_ranks
    ) == 1 and match_record.expected_ranks.issubset(dumps_ranks):
        # case two: alltoall or alltoall_base case.
        if match_record.has_undecided_case:
            alltoall_cases = [current_entry] + [
                all_entries[o][match_record.found_idx[o]]
                for o in match_record.found_ranks
            ]
            fail_check, total_input_numel, total_output_numel = check_size_alltoall(
                alltoall_cases
            )
            if major_v <= 2 and minor_v <= 3:
                # We don't log the input/output sizes for alltoall before v2.4,
                # so we don't consider the size mismatch as an error for now.
                fail_check = False
            if fail_check:
                # When we see errors in all_to_all, it's hard to tell which rank is the source of the error.
                mismatch[pg_name] += 1
                logger_msg = (
                    "Input/output mismatch in the collective sequence number: %s"
                )
                match_record.entry_state.log(
                    logger,
                    logger_msg,
                    format_frames,
                    total_numel=(total_input_numel, total_output_numel),
                )
                match_record.candidate_ranks.update(match_record.found_ranks)
                match_record.candidate_idx.update(match_record.found_idx)
                match_record.found_idx.clear()
                match_record.found_ranks.clear()
                match_record.errors.add(
                    (first_rank, MatchInfo(MatchState.SIZE_OR_SYNTAX_MISMATCH))
                )
            else:
                match_record.found_ranks.update(match_record.candidate_ranks)
                match_record.found_idx.update(match_record.candidate_idx)
                match_record.candidate_idx.clear()
                match_record.candidate_ranks.clear()
        # case three: all joined and everything matches on all ranks.
        else:
            match_record.found_ranks.update(match_record.candidate_ranks)
            match_record.found_idx.update(match_record.candidate_idx)
            match_record.candidate_idx.clear()
            match_record.candidate_ranks.clear()
    # case four: mismatch cases due to not same type, size mismatch or state mismatch.
    elif len(match_record.errors) > 0:
        mismatch[pg_name] += 1
        logger_msg = "Collective sequence number: %s has errors"
        match_record.entry_state.log(
            logger, logger_msg, format_frames, errors=match_record.errors
        )
        match_record.candidate_ranks.update(match_record.found_ranks)
        match_record.candidate_idx.update(match_record.found_idx)
        match_record.found_idx.clear()
        match_record.found_ranks.clear()
    # partial analysis case when we cannot decide what's wrong with this collective entry.
    else:
        match_record.candidate_ranks.update(match_record.found_ranks)
        match_record.candidate_idx.update(match_record.found_idx)
        match_record.found_idx.clear()
        match_record.found_ranks.clear()
        # if any element in expected_ranks not in dumps_ranks.
        if match_record.expected_ranks - dumps_ranks:
            mismatch[pg_name] += 1
            logger.info(
                "We cannot decide what's wrong with this collective entry "
                "because we missed FR dumps from ranks (%s) so we don't have enough "
                "information. If you want to debug further use -j to dump all raw trace",
                str(match_record.expected_ranks - dumps_ranks),
            )
        else:
            logger.info(
                "No errors found for this collective entry, There could be some "
                "other reasons why we see collective timeout."
            )