def test_different_types_schema_and_serialization(
    init_mode, write_method, are_types_optional, postgres
):
    table_name = postgres.random_table_name()

    if are_types_optional:

        class InputSchema(pw.Schema):
            a: str | None
            b: float | None
            c: bool | None
            d: list[int] | None
            e: tuple[int, int, int] | None
            f: pw.Json | None
            g: str
            h: str
            i: pw.PyObjectWrapper[SimpleObject] | None
            j: pw.Duration | None
            k: list[str] | None
            l: list[pw.Duration] | None
            m: list[list[str]] | None
            n: Any
            o: Any

    else:

        class InputSchema(pw.Schema):  # type:ignore
            a: str
            b: float
            c: bool
            d: list[int]
            e: tuple[int, int, int]
            f: pw.Json
            g: str
            h: str
            i: pw.PyObjectWrapper[SimpleObject]
            j: pw.Duration
            k: list[str]
            l: list[pw.Duration]
            m: list[list[str]]
            n: Any
            o: Any

    rows = [
        {
            "a": "foo",
            "b": 1.5,
            "c": False,
            "d": [1, 2, 3],
            "e": (1, 2, 3),
            "f": {"foo": "bar", "baz": 123},
            "g": "2025-03-14T10:13:00",
            "h": "2025-04-23T10:13:00+00:00",
            "i": pw.wrap_py_object(SimpleObject("test")),
            "j": pd.Timedelta("4 days 2 seconds 123 us 456 ns"),
            "k": ["abc", "def", "ghi"],
            "l": [
                pd.Timedelta("4 days 2 seconds 123 us 456 ns"),
                pd.Timedelta("1 days 2 seconds 3 us 4 ns"),
            ],
            "m": [["a", "b"], ["c", "d"]],
            "n": np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=int),
            "o": np.array(
                [[[1.1, 2.2], [3.3, 4.4]], [[5.5, 6.6], [7.7, 8.8]]], dtype=float
            ),
        }
    ]

    table = (
        pw.debug.table_from_rows(
            InputSchema,
            [tuple(row.values()) for row in rows],
        )
        .with_columns(
            g=pw.this.g.dt.strptime("%Y-%m-%dT%H:%M:%S", contains_timezone=False),
            h=pw.this.h.dt.strptime("%Y-%m-%dT%H:%M:%S%z", contains_timezone=True),
        )
        .update_types(n=np.ndarray[None, int], o=np.ndarray[None, float])  # type: ignore
    )
    if are_types_optional:
        table = table.update_types(
            g=pw.DateTimeNaive | None,
            h=pw.DateTimeUtc | None,
            n=np.ndarray[None, int] | None,  # type: ignore
            o=np.ndarray[None, float] | None,  # type: ignore
        )

    write_method(
        table,
        postgres_settings=POSTGRES_SETTINGS,
        table_name=table_name,
        init_mode=init_mode,
    )
    run()

    result = postgres.get_table_contents(table_name, InputSchema.column_names())

    for row in result:
        obj = api.deserialize(bytes(row["i"]))
        assert isinstance(
            obj, pw.PyObjectWrapper
        ), f"expecting PyObjectWrapper, got {type(obj)}"
        row["i"] = obj.value

    expected_output_row = {
        "a": "foo",
        "b": 1.5,
        "c": False,
        "d": [1, 2, 3],
        "e": [1, 2, 3],
        "f": {"foo": "bar", "baz": 123},
        "g": datetime.datetime(2025, 3, 14, 10, 13),
        "h": datetime.datetime(2025, 4, 23, 10, 13, tzinfo=datetime.timezone.utc),
        "i": SimpleObject("test"),
        "j": pd.Timedelta("4 days 2 seconds 123 us").value // 1_000,
        "k": ["abc", "def", "ghi"],
        "l": [
            pd.Timedelta("4 days 2 seconds 123 us").value // 1_000,
            pd.Timedelta("1 days 2 seconds 3 us").value // 1_000,
        ],
        "m": [["a", "b"], ["c", "d"]],
        "n": np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=int),
        "o": np.array(
            [[[1.1, 2.2], [3.3, 4.4]], [[5.5, 6.6], [7.7, 8.8]]], dtype=float
        ),
    }

    result = result[0]
    assert np.array_equal(result.pop("n"), expected_output_row.pop("n"))
    assert np.array_equal(result.pop("o"), expected_output_row.pop("o"))

    assert result == expected_output_row
    external_schema = postgres.get_table_schema(table_name)
    assert external_schema["a"].type_name == "text"
    assert external_schema["b"].type_name == "double precision"
    assert external_schema["c"].type_name == "boolean"
    assert external_schema["d"].type_name == "array"
    assert external_schema["e"].type_name == "array"
    assert external_schema["f"].type_name == "jsonb"
    assert external_schema["g"].type_name == "timestamp without time zone"
    assert external_schema["h"].type_name == "timestamp with time zone"
    assert external_schema["i"].type_name == "bytea"
    assert external_schema["j"].type_name == "bigint"
    assert external_schema["k"].type_name == "array"
    assert external_schema["l"].type_name == "array"
    assert external_schema["m"].type_name == "array"
    assert external_schema["n"].type_name == "array"
    assert external_schema["o"].type_name == "array"
    for column_name, column_props in external_schema.items():
        if column_name in ("time", "diff"):
            assert not column_props.is_nullable
            continue
        if column_name == "a":
            is_primary_key = write_method is not pw.io.postgres.write
            if is_primary_key:
                assert not column_props.is_nullable
                continue
        assert column_props.is_nullable == are_types_optional, column_name

    class TestObserver(pw.io.python.ConnectorObserver):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.n_rows_processed = 0

        def on_change(
            self, key: pw.Pointer, row: dict[str, Any], time: int, is_addition: bool
        ) -> None:
            self.n_rows_processed += 1
            assert row["a"] == "foo"
            assert row["b"] == 1.5
            assert not row["c"]
            assert row["d"] == (1, 2, 3)
            assert row["e"] == (1, 2, 3)
            assert row["f"] == pw.Json({"foo": "bar", "baz": 123})
            assert row["g"] == datetime.datetime(2025, 3, 14, 10, 13)
            assert row["h"] == datetime.datetime(
                2025, 4, 23, 10, 13, tzinfo=datetime.timezone.utc
            )
            assert row["i"].value == SimpleObject("test")
            assert row["j"] == pd.Timedelta("4 days 2 seconds 123 us")
            assert row["k"] == ("abc", "def", "ghi")
            assert row["l"] == (
                pd.Timedelta("4 days 2 seconds 123 us"),
                pd.Timedelta("1 days 2 seconds 3 us"),
            )
            assert row["m"] == (("a", "b"), ("c", "d"))

    observer = TestObserver()
    G.clear()
    table = pw.io.postgres.read(
        postgres_settings=POSTGRES_SETTINGS,
        table_name=table_name,
        schema=InputSchema,
        mode="static",
    )
    pw.io.python.write(table, observer)
    run()
    assert observer.n_rows_processed == 1