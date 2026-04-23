def just_print_entries(
    all_entries: dict[int, list[dict[str, Any]]],
    _groups: dict[str, Group],
    _memberships: dict[str, set[Any]],
    _pg_guids: dict[tuple[str, int], str],
    args: argparse.Namespace,
    stack_id_trace_map: dict[str, int],
) -> None:
    rows = []
    ranks = sorted(all_entries.keys())
    headers = [
        f"Rank {rank}"
        for rank in ranks
        if args.selected_ranks is None or rank in args.selected_ranks
    ]
    progress = True
    while progress:
        progress = False
        row = []
        for rank in ranks:
            if args.selected_ranks is not None and rank not in args.selected_ranks:
                continue
            if len(all_entries[rank]) == 0:
                row.append("")
            else:
                entry = all_entries[rank].pop(0)
                pg_name = _pg_guids[(entry["process_group"][0], rank)]
                if (
                    args.pg_filters is None
                    or entry["process_group"][1] in args.pg_filters
                    or entry["process_group"][0] in args.pg_filters
                ):
                    row.append(str(Op(entry, _memberships, pg_name)))
                else:
                    row.append("")
                progress = True
        if progress:
            rows.append(row)

    logger.info(tabulate(rows, headers=headers))

    if stack_id_trace_map and args.print_stack_trace:
        headers = ["stack_id", "frame_stack"]
        rows = []

        for frame, stack_id in sorted(
            stack_id_trace_map.items(), key=lambda item: item[1]
        ):
            rows.append([str(stack_id), frame])

        logger.info(tabulate(rows, headers=headers))