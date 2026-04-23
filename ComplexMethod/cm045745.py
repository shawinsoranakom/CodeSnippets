def test_mongodb_streaming_persistence(tmp_path, mongodb, plan):
    """Two-run persistence test for pw.io.mongodb.read in streaming mode.

    Run 1: the full collection snapshot appears in the output (all diff=+1).
    Run 2: only the delta since the previous run appears in the output.

    Each run is a fresh subprocess.Popen so no Rust/tokio global state from
    prior pw.run() calls (or daemon threads) in the test process is inherited.
    """
    pstorage_path = tmp_path / "PStorage"
    input_collection = mongodb.generate_collection_name()

    for doc in plan["initial"]:
        mongodb.insert_document(input_collection, doc)

    # --- Run 1: full collection must appear in the streaming output ---
    output_path_1 = tmp_path / "output_1.jsonl"
    run1_expected = plan["run1_expected"]
    p1 = _start_streaming_worker(output_path_1, pstorage_path, input_collection)
    try:
        _wait_and_terminate(
            FileLinesNumberChecker(output_path_1, len(run1_expected)), 30, p1
        )
    finally:
        if p1.poll() is None:
            p1.terminate()
            p1.wait()

    assert _sort_rows(
        [_extract_row(r) for r in read_jsonlines(output_path_1)]
    ) == _sort_rows(run1_expected), f"Run 1: expected {run1_expected}"

    # Apply changes to the MongoDB collection between the two runs.
    for op, filter_doc, new_doc in plan["changes"]:
        if op == "insert":
            mongodb.insert_document(input_collection, new_doc)
        elif op == "delete":
            mongodb.delete_document(input_collection, filter_doc)
        elif op == "replace":
            mongodb.replace_document(input_collection, filter_doc, new_doc)

    # --- Run 2: only the delta since Run 1 must appear ---
    output_path_2 = tmp_path / "output_2.jsonl"
    run2_expected = plan["run2_expected"]
    p2 = _start_streaming_worker(output_path_2, pstorage_path, input_collection)
    try:
        if run2_expected:
            _wait_and_terminate(
                FileLinesNumberChecker(output_path_2, len(run2_expected)), 30, p2
            )
        else:
            # no_changes: pre-create the output file so the checker can verify it
            # stays empty. double_check_interval gives the engine time to confirm
            # no events arrive before we declare success.
            output_path_2.touch()
            _wait_and_terminate(
                FileLinesNumberChecker(output_path_2, 0),
                30,
                p2,
                double_check_interval=3.0,
            )
    finally:
        if p2.poll() is None:
            p2.terminate()
            p2.wait()

    assert _sort_rows(
        [_extract_row(r) for r in read_jsonlines(output_path_2)]
    ) == _sort_rows(run2_expected), f"Run 2: expected {run2_expected}"