def test_mssql_cdc_expired_lsn(tmp_path, mssql):
    """A persisted LSN that predates the CDC retention window must surface
    a specific CdcLsnOutOfRetention error on restart so the user knows to
    drop the persistence directory.

    The test reproduces the scenario without patching persistence files: after
    run 1 is over we insert additional rows to advance the CDC max LSN, then
    call `sys.sp_cdc_cleanup_change_table` with that newer LSN as the low
    water mark.  The procedure moves the capture instance's `start_lsn`
    forward, so `fn_cdc_get_min_lsn` in run 2 reports a value strictly
    greater than the persisted LSN — exactly the condition the retention
    check catches.
    """
    table_name = mssql.random_table_name()
    mssql.execute_sql(
        f"CREATE TABLE {table_name} ("
        f"  id INT PRIMARY KEY,"
        f"  name NVARCHAR(100) NOT NULL"
        f")"
    )
    mssql.enable_cdc(table_name)
    mssql.insert_row(table_name, {"id": 1, "name": "Alice"})
    mssql.insert_row(table_name, {"id": 2, "name": "Bob"})

    pstorage_path = tmp_path / "PStorage"
    persistence_config = pw.persistence.Config(
        backend=pw.persistence.Backend.filesystem(pstorage_path)
    )

    # Run 1: populate persistence with a valid LSN.
    output_path_1 = tmp_path / "output_1.jsonl"
    wait_result_with_checker(
        FileLinesNumberChecker(output_path_1, 2),
        timeout_sec=60,
        target=_mssql_persistence_worker,
        kwargs={
            "connection_string": MSSQL_CONNECTION_STRING,
            "table_name": table_name,
            "output_path": str(output_path_1),
            "mode": "streaming",
            "persistence_config": persistence_config,
        },
    )
    assert len(read_jsonlines(output_path_1)) == 2

    # Force fn_cdc_get_min_lsn for this capture instance past the persisted
    # value.  `sys.sp_cdc_cleanup_change_table` advances the capture
    # instance's `start_lsn` to its `@low_water_mark`, which is exactly what
    # `fn_cdc_get_min_lsn` reads — so after the call the new minimum reported
    # to the connector is strictly greater than the LSN run 1 persisted.
    mssql.insert_row(table_name, {"id": 3, "name": "Charlie"})
    mssql.insert_row(table_name, {"id": 4, "name": "Dana"})

    capture_instance = f"dbo_{table_name}"
    deadline = time.time() + 30
    advanced = False
    while time.time() < deadline:
        mssql.cursor.execute("SELECT sys.fn_cdc_get_max_lsn()")
        max_row = mssql.cursor.fetchone()
        if max_row is not None and max_row[0] is not None:
            max_lsn = max_row[0]
            try:
                mssql.cursor.execute(
                    "EXEC sys.sp_cdc_cleanup_change_table "
                    "@capture_instance=%s, @low_water_mark=%s",
                    (capture_instance, max_lsn),
                )
                while mssql.cursor.nextset():
                    pass
            except Exception:
                pass
            mssql.cursor.execute(
                "SELECT sys.fn_cdc_get_min_lsn(%s)", (capture_instance,)
            )
            min_row = mssql.cursor.fetchone()
            if (
                min_row is not None
                and min_row[0] is not None
                and bytes(min_row[0]) >= bytes(max_lsn)
            ):
                advanced = True
                break
        time.sleep(1)
    assert advanced, "CDC cleanup did not advance fn_cdc_get_min_lsn within 30s"

    # Run 2: must fail fast with the specific retention error, not hang or
    # silently produce an empty delta.  We bypass wait_result_with_checker here
    # because it asserts the child exited with code 0, which contradicts the
    # expected behavior of this test.
    output_path_2 = tmp_path / "output_2.jsonl"
    error_path = tmp_path / "run2_error.log"
    p2 = multiprocessing.Process(
        target=_mssql_persistence_worker,
        kwargs={
            "connection_string": MSSQL_CONNECTION_STRING,
            "table_name": table_name,
            "output_path": str(output_path_2),
            "mode": "streaming",
            "persistence_config": persistence_config,
            "error_path": str(error_path),
        },
    )
    p2.start()
    try:
        p2.join(timeout=60)
    finally:
        if p2.is_alive():
            p2.terminate()
            p2.join()
    error_text = error_path.read_text() if error_path.exists() else ""
    assert (
        p2.exitcode is not None and p2.exitcode != 0
    ), f"Run 2 should have failed with CdcLsnOutOfRetention.\n{error_text}"
    assert (
        "persisted CDC position is outside the SQL Server retention window"
        in error_text
    ), f"Expected CdcLsnOutOfRetention error, got:\n{error_text}"