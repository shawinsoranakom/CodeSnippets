def test_rabbitmq_header_round_trip(rabbitmq_context, tmp_path: pathlib.Path):
    """Test that all Pathway types survive a write→read round-trip through headers.

    Values are JSON-encoded as AMQP strings on write and appear in
    _metadata.application_properties on read. json.loads recovers the JSON value.
    Types that map natively to JSON (bool, int, float, str, None, Json) are
    fully round-trippable. Other types (bytes, DateTime, Duration, ndarray,
    Pointer, PyObjectWrapper) are serialized following the same encoding as
    pw.io.jsonlines.write.
    """
    import base64

    output_file = tmp_path / "output.txt"

    G.clear()
    table = pw.debug.table_from_rows(
        HeaderRoundTripSchema,
        [
            (
                "hello",  # str
                42,  # int
                3.14,  # float
                True,  # bool
                pw.Json({"key": "value", "nested": [1, 2]}),  # Json
                b"\xde\xad\xbe\xef",  # bytes
                pw.DateTimeNaive("2025-03-14T10:13:00"),  # DateTimeNaive
                pw.DateTimeUtc("2025-03-14T10:13:00+00:00"),  # DateTimeUtc
                pd.Timedelta("1 days 2 hours 3 seconds"),  # Duration
                7,  # Optional[int] - populated
                (1, "abc"),  # tuple
                [10, 20, 30],  # list
                np.array([1, 2, 3]),  # ndarray int
                np.array([1.1, 2.2]),  # ndarray float
                pw.wrap_py_object(SimpleObject(42)),  # PyObjectWrapper
            ),
            (
                "",  # str empty
                -1,  # int negative
                0.0,  # float zero
                False,  # bool
                pw.Json(None),  # Json null
                b"",  # bytes empty
                pw.DateTimeNaive("2026-01-01T00:00:00"),
                pw.DateTimeUtc("2026-01-01T00:00:00+00:00"),
                pd.Timedelta("0"),  # Duration zero
                None,  # Optional[int] - null
                (0, ""),  # tuple
                [],  # list empty
                np.array([], dtype=np.int64),  # ndarray empty
                np.array([], dtype=np.float64),  # ndarray empty
                pw.wrap_py_object(SimpleObject(0)),
            ),
        ],
    )
    pw.io.rabbitmq.write(
        table,
        uri=RABBITMQ_STREAM_URI,
        stream_name=rabbitmq_context.stream_name,
        format="json",
        headers=[
            table.s_val,
            table.i_val,
            table.f_val,
            table.b_val,
            table.json_val,
            table.bytes_val,
            table.dt_naive_val,
            table.dt_utc_val,
            table.dur_val,
            table.opt_val,
            table.tuple_val,
            table.list_val,
            table.ndarray_int_val,
            table.ndarray_float_val,
            table.pyobj_val,
        ],
    )
    pw.run()

    time.sleep(1)

    G.clear()
    table = pw.io.rabbitmq.read(
        uri=RABBITMQ_STREAM_URI,
        stream_name=rabbitmq_context.stream_name,
        format="plaintext",
        mode="static",
        with_metadata=True,
    )
    pw.io.csv.write(table, output_file)

    wait_result_with_checker(
        CsvLinesNumberChecker(output_file, 2),
        WAIT_TIMEOUT_SECS,
    )

    result = pd.read_csv(output_file)
    for _, row in result.iterrows():
        metadata = json.loads(row["_metadata"])
        app_props = metadata["application_properties"]

        # All header names must be present
        for field in HeaderRoundTripSchema.column_names():
            assert field in app_props, f"Missing header '{field}'"

        # JSON-native types: exact round-trip via json.loads
        s = json.loads(app_props["s_val"])
        assert isinstance(s, str)

        i = json.loads(app_props["i_val"])
        assert isinstance(i, int)

        f = json.loads(app_props["f_val"])
        assert isinstance(f, float)

        b = json.loads(app_props["b_val"])
        assert isinstance(b, bool)

        j = json.loads(app_props["json_val"])
        assert isinstance(j, (dict, type(None)))

        opt = json.loads(app_props["opt_val"])
        assert isinstance(opt, (int, type(None)))

        # bytes: base64-encoded string
        bytes_str = json.loads(app_props["bytes_val"])
        assert isinstance(bytes_str, str)
        base64.b64decode(bytes_str)  # must not raise

        # DateTimeNaive / DateTimeUtc: string representation
        dt_naive_str = json.loads(app_props["dt_naive_val"])
        assert isinstance(dt_naive_str, str)

        dt_utc_str = json.loads(app_props["dt_utc_val"])
        assert isinstance(dt_utc_str, str)

        # Duration: integer (nanoseconds)
        dur_val = json.loads(app_props["dur_val"])
        assert isinstance(dur_val, int)

        # Tuple: JSON array
        tuple_val = json.loads(app_props["tuple_val"])
        assert isinstance(tuple_val, list)

        # List: JSON array
        list_val = json.loads(app_props["list_val"])
        assert isinstance(list_val, list)

        # ndarray int: JSON object with @shape and @elements
        ndarray_int = json.loads(app_props["ndarray_int_val"])
        assert isinstance(ndarray_int, dict)
        assert "shape" in ndarray_int
        assert "elements" in ndarray_int

        # ndarray float: JSON object with @shape and @elements
        ndarray_float = json.loads(app_props["ndarray_float_val"])
        assert isinstance(ndarray_float, dict)
        assert "shape" in ndarray_float
        assert "elements" in ndarray_float

        # PyObjectWrapper: base64-encoded bincode string
        pyobj_str = json.loads(app_props["pyobj_val"])
        assert isinstance(pyobj_str, str)
        base64.b64decode(pyobj_str)