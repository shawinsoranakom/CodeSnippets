def test_mongodb_read_persistence(tmp_path, mongodb, plan):
    """Two-run persistence test for pw.io.mongodb.read in static mode.

    Run 1: the full collection is reflected in the output (all diff=+1).
    Run 2: only the delta since the previous run appears in the output.
    """

    class InputSchema(pw.Schema):
        product: str
        qty: int

    pstorage_path = tmp_path / "PStorage"
    persistence_config = pw.persistence.Config(
        backend=pw.persistence.Backend.filesystem(pstorage_path)
    )
    input_collection = mongodb.generate_collection_name()

    for doc in plan["initial"]:
        mongodb.insert_document(input_collection, doc)

    def run_read(output_path: pathlib.Path) -> None:
        G.clear()
        table = pw.io.mongodb.read(
            connection_string=MONGODB_CONNECTION_STRING,
            database=MONGODB_BASE_NAME,
            collection=input_collection,
            schema=InputSchema,
            mode="static",
            name="mongodb_read_persistence_source",
        )
        pw.io.jsonlines.write(table, output_path)
        run(persistence_config=persistence_config)

    # --- Run 1: full collection must be reflected ---
    output_path_1 = tmp_path / "output_1.jsonl"
    run_read(output_path_1)
    run1_rows = read_jsonlines(output_path_1)
    assert _sort_rows([_extract_row(r) for r in run1_rows]) == _sort_rows(
        plan["run1_expected"]
    ), f"Run 1: expected {plan['run1_expected']}, got {run1_rows}"

    # Apply changes to the MongoDB collection between the two runs.
    for op, filter_doc, new_doc in plan["changes"]:
        if op == "insert":
            mongodb.insert_document(input_collection, new_doc)
        elif op == "delete":
            mongodb.delete_document(input_collection, filter_doc)
        elif op == "replace":
            mongodb.replace_document(input_collection, filter_doc, new_doc)

    # --- Run 2: only the delta must appear ---
    output_path_2 = tmp_path / "output_2.jsonl"
    run_read(output_path_2)
    run2_rows = read_jsonlines(output_path_2)
    assert _sort_rows([_extract_row(r) for r in run2_rows]) == _sort_rows(
        plan["run2_expected"]
    ), f"Run 2: expected {plan['run2_expected']}, got {run2_rows}"