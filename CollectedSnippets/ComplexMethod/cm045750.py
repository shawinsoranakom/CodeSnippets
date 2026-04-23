def test_postgres_input(tmp_path, postgres, postgres_with_tls, with_tls):
    class InputSchema(pw.Schema):
        id: int = pw.column_definition(primary_key=True)
        v_none: bool | None
        v_bool: bool
        v_int: int
        v_float: float
        v_string: str
        v_bytes: bytes
        v_int_array: np.ndarray[None, int]  # type: ignore
        v_float_array: np.ndarray[None, float]  # type: ignore
        v_datetime_naive: pw.DateTimeNaive
        v_datetime_utc: pw.DateTimeUtc
        v_duration: pw.Duration
        v_json: pw.Json
        v_pyobject: bytes
        v_int_list: list[list[int]]
        v_float_list: list[list[float]]
        v_string_matrix: list[list[str]]
        v_bytes_matrix: list[list[bytes]]

    if with_tls:
        postgres = postgres_with_tls
        postgres_settings = copy.deepcopy(POSTGRES_WITH_TLS_SETTINGS)
        postgres_settings["sslmode"] = "verify-ca"
        postgres_settings["sslrootcert"] = str(CREDENTIALS_DIR / "ca.crt")
    else:
        postgres_settings = POSTGRES_SETTINGS

    output_path = tmp_path / "output.jsonl"
    table_name = postgres.random_table_name()
    create_table_sql = f"""
        CREATE TABLE {table_name} (
            id BIGSERIAL PRIMARY KEY,
            v_none BOOLEAN,
            v_bool BOOLEAN,
            v_int BIGINT,
            v_float DOUBLE PRECISION,
            v_string TEXT,
            v_bytes BYTEA,
            v_int_array BIGINT[],
            v_float_array DOUBLE PRECISION[],
            v_datetime_naive TIMESTAMP,
            v_datetime_utc TIMESTAMPTZ,
            v_duration INTERVAL,
            v_json JSONB,
            v_pyobject BYTEA,
            v_int_list BIGINT[],
            v_float_list DOUBLE PRECISION[],
            v_string_matrix TEXT[],
            v_bytes_matrix BYTEA[]
        );
    """
    postgres.execute_sql(create_table_sql)

    with postgres.publication(table_name) as publication_name:
        json_value_dumped = json.dumps({"key": "value"})
        insert_row_sql = f"""
            INSERT INTO {table_name} (
                v_none,
                v_bool,
                v_int,
                v_float,
                v_string,
                v_bytes,
                v_int_array,
                v_float_array,
                v_datetime_naive,
                v_datetime_utc,
                v_duration,
                v_json,
                v_pyobject,
                v_int_list,
                v_float_list,
                v_string_matrix,
                v_bytes_matrix
            ) VALUES (
                null,
                TRUE,
                42,
                3.1415926535,
                'hello world',
                '\\xDEADBEEF'::bytea,
                ARRAY[1, 2, 3, 4],
                ARRAY[1.1, 2.2, 3.3],
                '2025-01-01 12:00:00',
                '2025-01-01 12:00:00+00',
                INTERVAL '1 hour 30 minutes',
                '{json_value_dumped}',
                '\\xABCDEF'::bytea,
                ARRAY[[1, 2], [3, 4]],
                ARRAY[[1.1, 2.2], [3.3, 4.4]],
                ARRAY[['a}},{{', '{{,,,,,,{{b'], ['c,,', ',,d']],
                ARRAY[
                    ['\\xDEAD'::bytea, '\\xBEEF'::bytea],
                    ['\\xABCD'::bytea, '\\xEF01'::bytea]
                ]
            );
        """
        postgres.execute_sql(insert_row_sql)

        table = pw.io.postgres.read(
            postgres_settings=postgres_settings,
            table_name=table_name,
            schema=InputSchema,
            mode="streaming",
            publication_name=publication_name,
            autocommit_duration_ms=10,
        )
        pw.io.jsonlines.write(table, output_path)

        def stream_target():
            for i in range(5):
                wait_result_with_checker(
                    FileLinesNumberChecker(output_path, i + 1), 30, target=None
                )
                postgres.execute_sql(insert_row_sql)
            for i in range(5):
                wait_result_with_checker(
                    FileLinesNumberChecker(output_path, 6 + i), 30, target=None
                )
                delete_row_sql = f"DELETE FROM {table_name} WHERE id = {i + 1};"
                postgres.execute_sql(delete_row_sql)

        stream_thread = threading.Thread(target=stream_target, daemon=True)
        stream_thread.start()

        wait_result_with_checker(FileLinesNumberChecker(output_path, 11), 60)

    ids = set()
    with open(output_path, "r") as f:
        for row in f:
            data = json.loads(row)
            row_id = data.pop("id")
            data.pop("time")
            diff = data.pop("diff")
            if diff == 1:
                assert row_id not in ids
                ids.add(row_id)
            elif diff == -1:
                assert row_id in ids
                ids.remove(row_id)
            else:
                raise ValueError(f"unexpected diff: {diff}")
            assert data == {
                "v_none": None,
                "v_bool": True,
                "v_int": 42,
                "v_float": 3.1415926535,
                "v_string": "hello world",
                "v_bytes": "3q2+7w==",
                "v_int_array": {"shape": [4], "elements": [1, 2, 3, 4]},
                "v_float_array": {"shape": [3], "elements": [1.1, 2.2, 3.3]},
                "v_datetime_naive": "2025-01-01T12:00:00.000000000",
                "v_datetime_utc": "2025-01-01T12:00:00.000000000+0000",
                "v_duration": 5400000000000,
                "v_json": {"key": "value"},
                "v_pyobject": "q83v",
                "v_int_list": [[1, 2], [3, 4]],
                "v_float_list": [[1.1, 2.2], [3.3, 4.4]],
                "v_string_matrix": [["a},{", "{,,,,,,{b"], ["c,,", ",,d"]],
                "v_bytes_matrix": [["3q0=", "vu8="], ["q80=", "7wE="]],
            }
    assert len(ids) == 1