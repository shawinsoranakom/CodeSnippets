def test_iterate_persistence_sort_propagation(
    scenario_name, persistence_mode, tmp_path
):
    """Iterate + sort chunk-splitting with persistence across multiple runs.

    See CHUNK_SCENARIOS for scenario documentation. Each run:
    1. Applies file additions/modifications to the input directory.
    2. Runs the pipeline (iterate + sort) with the same persistence storage.
    3. Verifies the CSV output contains exactly the expected diffs.
    """
    input_path = tmp_path / "input"
    os.makedirs(input_path)
    output_path = tmp_path / "out.csv"
    pstorage_path = tmp_path / "PStorage"

    runs = CHUNK_SCENARIOS[scenario_name]

    # Accumulated event state across runs
    events: dict = {}
    prev_output_rows: set = set()
    accumulated_state: dict = {}  # (event_time, data, chunk_start) → multiplicity

    for run_idx, run_changes in enumerate(runs):
        # --- Apply changes to event state and write files ---
        for event_id, event_data in run_changes.items():
            if event_data is None:
                events.pop(event_id, None)
                filepath = input_path / f"{event_id}.csv"
                if filepath.exists():
                    os.remove(filepath)
            else:
                events[event_id] = event_data
                event_time, flag, data = event_data
                filepath = input_path / f"{event_id}.csv"
                write_lines(
                    filepath,
                    [
                        "event_time,flag,data",
                        f"{event_time},{flag},{data}",
                    ],
                )

        # --- Compute expected output ---
        assignments = _compute_chunk_assignments(events)
        curr_output_rows = _output_rows(events, assignments)
        expected_diffs = _compute_expected_diffs(prev_output_rows, curr_output_rows)
        assert expected_diffs, (
            f"Run {run_idx + 1} of '{scenario_name}' produces no diffs — "
            "this means it doesn't test persistence (nothing changed)"
        )
        prev_output_rows = curr_output_rows

        # --- Build and run pipeline ---
        G.clear()
        t = pw.io.csv.read(input_path, schema=EventSchema, mode="static")
        result = _build_chunk_propagation_pipeline(t)
        pw.io.csv.write(
            result.select(pw.this.event_time, pw.this.data, pw.this.chunk_start),
            output_path,
        )
        run(
            persistence_config=pw.persistence.Config(
                pw.persistence.Backend.filesystem(pstorage_path),
                persistence_mode=persistence_mode,
            )
        )

        # --- Verify diffs ---
        _assert_diffs_match(output_path, expected_diffs)

        # --- Verify accumulated state ---
        # Apply this run's diffs to the running state and check that every row
        # has multiplicity exactly 1. With diff amplification (the concat bug),
        # applying e.g. diff=-4 to a row with multiplicity +1 would produce -3,
        # which is an impossible state for a table where each row exists once.
        try:
            df = pd.read_csv(output_path)
            for _, row in df.iterrows():
                key = (int(row["event_time"]), row["data"], int(row["chunk_start"]))
                accumulated_state[key] = accumulated_state.get(key, 0) + int(
                    row["diff"]
                )
        except pd.errors.EmptyDataError:
            pass

        for key, mult in accumulated_state.items():
            assert mult in (0, 1), (
                f"Run {run_idx + 1} of '{scenario_name}': row {key} has "
                f"multiplicity {mult} (expected 0 or 1)"
            )

        # The set of rows with multiplicity 1 must equal the expected full state
        active_rows = {k for k, v in accumulated_state.items() if v == 1}
        assert active_rows == curr_output_rows, (
            f"Run {run_idx + 1} of '{scenario_name}': accumulated state "
            f"doesn't match expected.\n"
            f"  missing: {curr_output_rows - active_rows}\n"
            f"  extra:   {active_rows - curr_output_rows}"
        )