def test_postgres_date_out_of_range_skipped(tmp_path, postgres):
    """Rows with dates/timestamps outside chrono's supported nanosecond range must be
    skipped with a warning, without crashing the reader. Valid rows must still appear.
    Covers DATE, TIMESTAMP, and TIMESTAMP WITH TIME ZONE column types."""

    class InputSchema(pw.Schema):
        id: str = pw.column_definition(primary_key=True)
        birthday: pw.DateTimeNaive
        created_at: pw.DateTimeNaive
        updated_at: pw.DateTimeUtc
        value: str

    output_path = tmp_path / "output.jsonl"
    table_name = postgres.random_table_name()

    postgres.execute_sql(
        f"""
        CREATE TABLE {table_name} (
            id UUID PRIMARY KEY,
            birthday DATE NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            value TEXT NOT NULL
        );
        """
    )

    VALID_SNAPSHOT_ID = "a0000000-0000-0000-0000-000000000001"
    OOR_DATE_PAST_ID = "b0000000-0000-0000-0000-000000000002"  # DATE 0001-01-01
    OOR_DATE_FUTURE_ID = "c0000000-0000-0000-0000-000000000003"  # DATE 9999-12-31
    OOR_TS_PAST_ID = "d0000000-0000-0000-0000-000000000004"  # TIMESTAMP 0001-01-01
    OOR_TS_FUTURE_ID = "e0000000-0000-0000-0000-000000000005"  # TIMESTAMP 9999-12-31
    OOR_TSZ_PAST_ID = "f0000000-0000-0000-0000-000000000006"  # TIMESTAMPTZ 0001-01-01
    OOR_TSZ_FUTURE_ID = "a0000000-0000-0000-0000-000000000007"  # TIMESTAMPTZ 9999-12-31
    VALID_STREAMING_ID = "b0000000-0000-0000-0000-000000000008"

    # (id, birthday, created_at, updated_at, value)
    VALID_DATE = "2025-03-14"
    VALID_TS = "2025-03-14 12:00:00"
    VALID_TSZ = "2025-03-14 12:00:00+00"
    OOR_PAST_DATE = "0001-01-01"
    OOR_FUTURE_DATE = "9999-12-31"
    OOR_PAST_TS = "0001-01-01 00:00:00"
    OOR_FUTURE_TS = "9999-12-31 23:59:59"
    OOR_PAST_TSZ = "0001-01-01 00:00:00+00"
    OOR_FUTURE_TSZ = "9999-12-31 23:59:59+00"

    snapshot_inserts = [
        (VALID_SNAPSHOT_ID, VALID_DATE, VALID_TS, VALID_TSZ, "valid_snapshot"),
        (OOR_DATE_PAST_ID, OOR_PAST_DATE, VALID_TS, VALID_TSZ, "oor_date_past"),
        (OOR_DATE_FUTURE_ID, OOR_FUTURE_DATE, VALID_TS, VALID_TSZ, "oor_date_future"),
        (OOR_TS_PAST_ID, VALID_DATE, OOR_PAST_TS, VALID_TSZ, "oor_ts_past"),
        (OOR_TS_FUTURE_ID, VALID_DATE, OOR_FUTURE_TS, VALID_TSZ, "oor_ts_future"),
        (OOR_TSZ_PAST_ID, VALID_DATE, VALID_TS, OOR_PAST_TSZ, "oor_tsz_past"),
        (OOR_TSZ_FUTURE_ID, VALID_DATE, VALID_TS, OOR_FUTURE_TSZ, "oor_tsz_future"),
    ]
    for rid, birthday, created_at, updated_at, val in snapshot_inserts:
        postgres.execute_sql(
            f"""
            INSERT INTO {table_name} (id, birthday, created_at, updated_at, value)
            VALUES ('{rid}', '{birthday}', '{created_at}', '{updated_at}', '{val}');
            """
        )

    OOR_IDS = {
        OOR_DATE_PAST_ID,
        OOR_DATE_FUTURE_ID,
        OOR_TS_PAST_ID,
        OOR_TS_FUTURE_ID,
        OOR_TSZ_PAST_ID,
        OOR_TSZ_FUTURE_ID,
    }
    # 1 valid snapshot row + 1 valid streaming row
    n_expected = 2

    with postgres.publication(table_name) as publication_name:
        table = pw.io.postgres.read(
            postgres_settings=POSTGRES_SETTINGS,
            table_name=table_name,
            schema=InputSchema,
            mode="streaming",
            publication_name=publication_name,
            autocommit_duration_ms=10,
        )
        pw.io.jsonlines.write(table, output_path)

        def stream_target():
            wait_result_with_checker(
                FileLinesNumberChecker(output_path, 1), 30, target=None
            )
            postgres.execute_sql(
                f"""
                INSERT INTO {table_name} (id, birthday, created_at, updated_at, value)
                VALUES (
                    '{VALID_STREAMING_ID}', '{VALID_DATE}', '{VALID_TS}', '{VALID_TSZ}',
                    'valid_streaming'
                );
                """
            )

        stream_thread = threading.Thread(target=stream_target, daemon=True)
        stream_thread.start()
        wait_result_with_checker(FileLinesNumberChecker(output_path, n_expected), 30)

    rows_out = []
    with open(output_path) as f:
        for line in f:
            rows_out.append(json.loads(line))

    assert len(rows_out) == n_expected

    ids_out = {r["id"] for r in rows_out}
    assert VALID_SNAPSHOT_ID in ids_out, "Valid snapshot row must be present"
    assert VALID_STREAMING_ID in ids_out, "Valid streaming row must be present"
    for oor_id in OOR_IDS:
        assert oor_id not in ids_out, f"Out-of-range row {oor_id} must be skipped"