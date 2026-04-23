def test_synchronization_group(tmp_path, plan, type_):
    input_path_1 = tmp_path / "input_1"
    input_path_2 = tmp_path / "input_2"
    os.mkdir(input_path_1)
    os.mkdir(input_path_2)

    if type_ == "Int":
        max_difference = 10
    elif type_ in ("DateTimeUtc", "DateTimeNaive", "Duration"):
        max_difference = datetime.timedelta(seconds=10)
    else:
        raise ValueError(f"Unexpected type: {type_}")

    def stream_inputs(input_path: pathlib.Path, plan: list[dict]):
        time.sleep(1)
        for index, entry in enumerate(plan):
            raw_value = entry["k"]
            prepared_entry = {"v": entry["v"]}
            if type_ == "Int":
                prepared_entry["k"] = raw_value
            elif type_ == "Duration":
                prepared_entry["k"] = raw_value * 1_000_000_000
            elif type_ == "DateTimeUtc":
                prepared_entry["k"] = datetime.datetime.fromtimestamp(
                    raw_value, tz=datetime.timezone.utc
                ).isoformat()
            elif type_ == "DateTimeNaive":
                prepared_entry["k"] = datetime.datetime.fromtimestamp(
                    raw_value
                ).isoformat()
            else:
                raise ValueError(f"Unexpected type: {type_}")
            with open(input_path / f"{index}.jsonl", "w") as f:
                json.dump(prepared_entry, f)
            time.sleep(0.5)

    output_path = tmp_path / "output.csv"

    if type_ == "Int":
        TrackedFieldType = int
    elif type_ == "Duration":
        TrackedFieldType = pw.Duration
    elif type_ == "DateTimeUtc":
        TrackedFieldType = pw.DateTimeUtc
    elif type_ == "DateTimeNaive":
        TrackedFieldType = pw.DateTimeNaive
    else:
        raise ValueError(f"Unexpected type: {type_}")

    class InputSchema(pw.Schema):
        k: TrackedFieldType
        v: str

    table_1 = pw.io.jsonlines.read(
        input_path_1, schema=InputSchema, autocommit_duration_ms=20
    )
    table_2 = pw.io.jsonlines.read(
        input_path_2, schema=InputSchema, autocommit_duration_ms=20
    )
    table_1.promise_universes_are_disjoint(table_2)
    table_merged = table_1.concat(table_2)
    pw.io.register_input_synchronization_group(
        pw.io.SynchronizedColumn(table_1.k, **plan.get("sync_params_1", {})),
        pw.io.SynchronizedColumn(table_2.k, **plan.get("sync_params_2", {})),
        max_difference=max_difference,
    )
    pw.io.csv.write(table_merged, output_path)

    inputs_thread_1 = threading.Thread(
        target=stream_inputs, args=(input_path_1, plan["source_1"]), daemon=True
    )
    inputs_thread_1.start()
    inputs_thread_2 = threading.Thread(
        target=stream_inputs, args=(input_path_2, plan["source_2"]), daemon=True
    )
    inputs_thread_2.start()

    wait_result_with_checker(
        CsvLinesNumberChecker(output_path, plan["expected_entries"]),
        99,
        double_check_interval=3.0,
    )
    inputs_thread_1.join()
    inputs_thread_2.join()

    checker = CsvLinesNumberChecker(output_path, plan["expected_entries"])
    assert checker()