def test_different_types_serialization(
    tmp_path: pathlib.Path, data_format, with_optionals, serialization_tester
):
    auxiliary_path = tmp_path / "auxiliary-storage"

    table, known_rows = serialization_tester.create_variety_table(with_optionals)
    if data_format == "delta" or data_format == "delta_stored_schema":
        pw.io.deltalake.write(table, auxiliary_path)
    elif data_format == "json":
        pw.io.jsonlines.write(table, auxiliary_path)
    elif data_format == "csv":
        pw.io.csv.write(table, auxiliary_path)
    else:
        raise ValueError(f"Unknown data format: {data_format}")
    run_all()
    G.clear()

    class Checker:
        def __init__(self):
            self.n_processed_rows = 0

        def __call__(self, key, row, time, is_addition):
            self.n_processed_rows += 1
            column_values = known_rows[row["pkey"]]
            for field, expected_value in column_values.items():
                if isinstance(expected_value, np.ndarray):
                    assert row[field].shape == expected_value.shape
                    assert (row[field] == expected_value).all()
                else:
                    expected_values = [expected_value]
                    if data_format == "csv" and expected_value is None:
                        # Impossible to parse unambiguosly, hence allowing string "None"
                        # or base64-decoded option
                        if field == "string":
                            expected_values.append("None")
                        elif field == "binary_data":
                            expected_values.append(base64.b64decode("None"))

                    assert row[field] in expected_values

    InputSchema = table.schema
    if data_format == "delta":
        table = pw.io.deltalake.read(auxiliary_path, schema=InputSchema, mode="static")
    elif data_format == "delta_stored_schema":
        table = pw.io.deltalake.read(auxiliary_path, mode="static")
    elif data_format == "json":
        table = pw.io.jsonlines.read(auxiliary_path, schema=InputSchema, mode="static")
    elif data_format == "csv":
        table = pw.io.csv.read(auxiliary_path, schema=InputSchema, mode="static")
    else:
        raise ValueError(f"Unknown data format: {data_format}")
    checker = Checker()
    pw.io.subscribe(table, on_change=checker)
    run_all()
    assert checker.n_processed_rows == len(known_rows)