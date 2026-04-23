def _compute_and_print_single(
    table: Table,
    captured: api.CapturedStream,
    *,
    squash_updates: bool,
    include_id: bool,
    short_pointers: bool,
    n_rows: int | None,
    terminate_on_error: bool,
) -> None:
    columns = list(table._columns.keys())
    if squash_updates:
        output_data = list(
            api.squash_updates(captured, terminate_on_error=terminate_on_error).items()
        )
    else:
        columns.extend([api.TIME_PSEUDOCOLUMN, api.DIFF_PSEUDOCOLUMN])
        output_data = []
        for row in captured:
            output_data.append((row.key, tuple(row.values) + (row.time, row.diff)))

    if not columns and not include_id:
        return

    if include_id or len(columns) > 1:
        none = ""
    else:
        none = "None"

    def _format(x):
        if x is None:
            return none
        if isinstance(x, api.Pointer) and short_pointers:
            s = str(x)
            if len(s) > 8:
                s = s[:8] + "..."
            return s
        return str(x)

    if squash_updates:

        def _key(row: tuple[api.Pointer, tuple[api.Value, ...]]):
            return tuple(_NoneAwareComparisonWrapper(value) for value in row[1]) + (
                row[0],
            )

    else:
        # sort by time and diff first if there is no squashing
        def _key(row: tuple[api.Pointer, tuple[api.Value, ...]]):
            return (
                row[1][-2:]
                + tuple(_NoneAwareComparisonWrapper(value) for value in row[1])
                + (row[0],)
            )

    try:
        output_data = sorted(output_data, key=_key)
    except (ValueError, TypeError):
        pass  # Some values (like arrays, PyObjectWrapper) cannot be sorted this way, so just don't sort them.
    output_data_truncated = itertools.islice(output_data, n_rows)
    data = []
    if include_id:
        name = "" if columns else "id"
        data.append([name] + columns)
    else:
        data.append(columns)
    for key, values in output_data_truncated:
        formatted_row = []
        if include_id:
            formatted_row.append(_format(key))
        formatted_row.extend(_format(value) for value in values)
        data.append(formatted_row)
    max_lens = [max(len(row[i]) for row in data) for i in range(len(data[0]))]
    max_lens[-1] = 0
    for formatted_row in data:
        formatted = " | ".join(
            value.ljust(max_len) for value, max_len in zip(formatted_row, max_lens)
        )
        print(formatted.rstrip())