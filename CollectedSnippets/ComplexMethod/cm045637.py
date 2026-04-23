def test_delta_snapshot_mode_rewind(tmp_path):
    input_path = tmp_path / "input.jsonl"
    delta_table_path = tmp_path / "delta"
    output_path = tmp_path / "output.jsonl"
    pstorage_path = tmp_path / "PStorage"

    row_1 = {
        "key": 1,
        "value": "one",
    }
    row_2 = {
        "key": 2,
        "value": "two",
    }
    row_3 = {
        "key": 3,
        "value": "three",
    }

    class InputSchema(pw.Schema):
        key: int = pw.column_definition(primary_key=True)
        value: str

    def update_delta_table_snapshot(rows: list[dict]):
        G.clear()
        with open(input_path, "w") as f:
            for row in rows:
                f.write(json.dumps(row))
                f.write("\n")
        table = pw.io.jsonlines.read(input_path, schema=InputSchema, mode="static")
        pw.io.deltalake.write(table, delta_table_path, output_table_type="snapshot")
        run_all(
            persistence_config=pw.persistence.Config(
                backend=pw.persistence.Backend.filesystem(pstorage_path)
            )
        )

    def from_delta_table_to_file(start_from_timestamp_ms: int | None) -> list[dict]:
        G.clear()
        table = pw.io.deltalake.read(
            delta_table_path,
            schema=InputSchema,
            mode="static",
            start_from_timestamp_ms=start_from_timestamp_ms,
        )
        pw.io.jsonlines.write(table, output_path)
        run_all()
        result = []
        with open(output_path, "r") as f:
            for row in f:
                parsed_row = json.loads(row)
                if start_from_timestamp_ms is None:
                    assert parsed_row["diff"] == 1
                result.append(parsed_row)
        return result

    time_start_1 = int(time.time() * 1000)
    time.sleep(0.05)
    update_delta_table_snapshot([row_1, row_2, row_3])
    assert len(from_delta_table_to_file(None)) == 3

    time_start_2 = int(time.time() * 1000)
    time.sleep(0.05)
    update_delta_table_snapshot([row_1, row_2])
    assert len(from_delta_table_to_file(None)) == 2

    time_start_3 = int(time.time() * 1000)
    time.sleep(0.05)
    update_delta_table_snapshot([row_1, row_3])
    assert len(from_delta_table_to_file(None)) == 2

    time_start_4 = int(time.time() * 1000)
    time.sleep(0.05)
    update_delta_table_snapshot([row_2])
    assert len(from_delta_table_to_file(None)) == 1
    time.sleep(0.05)
    time_start_5 = int(time.time() * 1000)

    # We start with an empty set.
    # Then, we move to [1, 2, 3]. It's 3 actions.
    # Then, we move to [1, 2] via just one action: -1. It's 4 actions in total.
    # Then, we move to [1, 3], which takes -2, +3. It's 6 actions in total.
    # Then, we move to [2], which takes -1, -3, +2. It's 9 actions.
    assert len(from_delta_table_to_file(time_start_1)) == 9

    # We the state at `time_start_2` corresponds to the snapshot with 3 elements.
    # Then we apply all diffs, so the size of the log is the same as in the previous
    # case.
    assert len(from_delta_table_to_file(time_start_2)) == 9

    # We start with [1, 2]. It's 2 events.
    # Then, we do -2, +3 to advance to [1, 3]. It's 4 events.
    # Then, we do -1, -3, +2 to advance to [2]. It's 7 events.
    assert len(from_delta_table_to_file(time_start_3)) == 7

    # We start with [1, 3]. It's 2 events.
    # Then, we do -1, -3, +2 to advance to [2]. It's 5 events.
    assert len(from_delta_table_to_file(time_start_4)) == 5

    # There are no events following after `time_start_5`, so we take the snapshot
    # that is actual at this point of time. It's just one action: [2]
    assert len(from_delta_table_to_file(time_start_5)) == 1