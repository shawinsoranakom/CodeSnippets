def visualize_ops(
        match: bool,
        _pg_guids: dict[tuple[str, int], str],
    ) -> None:
        all_ops = {
            rank: [
                Op(e, memberships, _pg_guids[(e["process_group"][0], rank)])
                for _, e in all_rank_events[rank]
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
        logger.info("%s", tabulate(table))