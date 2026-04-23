def test_different_types_schema_and_serialization(init_mode, are_types_optional, mysql):
    table_name = mysql.random_table_name()

    if are_types_optional:

        class InputSchema(pw.Schema):
            a: str | None
            b: float | None
            c: bool | None
            d: bytes | None
            e: api.Pointer | None
            f: pw.Json | None
            g: str
            h: str
            i: pw.PyObjectWrapper[SimpleObject] | None
            j: pw.Duration | None
            k: int | None
            l: pw.Duration | None

    else:

        class InputSchema(pw.Schema):  # type:ignore
            a: str
            b: float
            c: bool
            d: bytes
            e: api.Pointer
            f: pw.Json
            g: str
            h: str
            i: pw.PyObjectWrapper[SimpleObject]
            j: pw.Duration
            k: int
            l: pw.Duration

    rows = [
        {
            "a": "foo",
            "b": 1.5,
            "c": False,
            "d": bytes([0xFF, 0xFE, 0xC0, 0xC1]),
            "e": api.ref_scalar(42),
            "f": {"foo": "bar", "baz": 123},
            "g": "2025-03-14T10:13:00",
            "h": "2025-04-23T10:13:00+00:00",
            "i": pw.wrap_py_object(SimpleObject("test")),
            "j": pd.Timedelta("4 days 2 seconds 123 us 456 ns"),
            "k": 42,
            "l": -pd.Timedelta("5 days 6 minutes 7 seconds 8 ms 9 us"),
        }
    ]

    table = pw.debug.table_from_rows(
        InputSchema,
        [tuple(row.values()) for row in rows],
    ).with_columns(
        g=pw.this.g.dt.strptime("%Y-%m-%dT%H:%M:%S", contains_timezone=False),
        h=pw.this.h.dt.strptime("%Y-%m-%dT%H:%M:%S%z", contains_timezone=True),
    )
    if are_types_optional:
        table = table.update_types(
            g=pw.DateTimeNaive | None,
            h=pw.DateTimeUtc | None,
        )

    pw.io.mysql.write(
        table,
        connection_string=MYSQL_CONNECTION_STRING,
        table_name=table_name,
        init_mode=init_mode,
    )
    pw.run()

    result = mysql.get_table_contents(table_name, InputSchema.column_names())

    for row in result:
        obj = api.deserialize(bytes(row["i"]))
        assert isinstance(
            obj, pw.PyObjectWrapper
        ), f"expecting PyObjectWrapper, got {type(obj)}"
        row["i"] = obj.value

    expected_result = {
        "a": "foo",
        "b": 1.5,
        "c": False,
        "d": bytes([0xFF, 0xFE, 0xC0, 0xC1]),
        "e": "^Z5QKEQCDK9ZZ6TSYV0PM0G92JC",
        "f": {"foo": "bar", "baz": 123},
        "g": datetime.datetime(2025, 3, 14, 10, 13),
        "h": datetime.datetime(2025, 4, 23, 10, 13),
        "i": SimpleObject("test"),
        "j": pd.Timedelta("4 days 2 seconds 123 us"),
        "k": 42,
        "l": -pd.Timedelta("5 days 6 minutes 7 seconds 8 ms 9 us"),
    }
    assert len(result) == 1
    for key, expected_value in expected_result.items():
        our_value = result[0][key]
        if key == "f":
            our_value = json.loads(our_value)
        assert our_value == expected_value, key

    external_schema = mysql.get_table_schema(table_name)
    assert external_schema["a"].type_name == "text"
    assert external_schema["b"].type_name == "double"
    assert external_schema["c"].type_name == "tinyint"
    assert external_schema["d"].type_name == "blob"
    assert external_schema["e"].type_name == "text"
    assert external_schema["f"].type_name == "json"
    assert external_schema["g"].type_name == "datetime"
    assert external_schema["h"].type_name == "datetime"
    assert external_schema["i"].type_name == "blob"
    assert external_schema["j"].type_name == "time"
    assert external_schema["k"].type_name == "bigint"
    assert external_schema["l"].type_name == "time"
    for column_name, column_props in external_schema.items():
        if column_name in ("time", "diff"):
            assert not column_props.is_nullable
        else:
            assert column_props.is_nullable == are_types_optional, column_name