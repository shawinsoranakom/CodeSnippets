def attempt_to_make_names_unique(entries_and_traces):
    names, non_unique_names = (set(), set())

    def all_the_same(items) -> bool:
        return all(i == items[0] for i in items)

    for entry, _ in entries_and_traces:
        if entry["name"] in names:
            non_unique_names.add(entry["name"])
        else:
            names.add(entry["name"])

    for name in non_unique_names:
        entries_and_traces_with_name = [
            (entry, trace)
            for entry, trace in entries_and_traces
            if entry["name"] == name
        ]

        zipped_traces = list(zip(*[trace for _, trace in entries_and_traces_with_name]))
        first_trace_difference = next(
            (
                i
                for i, trace_eles in enumerate(zipped_traces)
                if not all_the_same(trace_eles)
            ),
            None,
        )

        if first_trace_difference is None:
            # can't create a unique name, leave the names as they
            # are they will get aggregated by the pivot_table call
            continue

        for entry, trace in entries_and_traces_with_name:
            entry["name"] = " <- ".join(
                (entry["name"],) + trace[: first_trace_difference + 1]
            )