def test_py_object_wrapper_serialization(tmp_path: pathlib.Path, data_format):
    input_path = tmp_path / "input.jsonl"
    auxiliary_path = tmp_path / "auxiliary-storage"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text("test")

    table = pw.io.plaintext.read(input_path, mode="static")
    table = table.select(
        data=pw.this.data, fun=pw.wrap_py_object(len, serializer=pickle)  # type: ignore
    )
    if data_format == "delta":
        pw.io.deltalake.write(table, auxiliary_path)
    elif data_format == "json":
        pw.io.jsonlines.write(table, auxiliary_path)
    elif data_format == "csv":
        pw.io.csv.write(table, auxiliary_path)
    else:
        raise ValueError(f"Unknown data format: {data_format}")
    run_all()
    G.clear()

    class InputSchema(pw.Schema):
        data: str = pw.column_definition(primary_key=True)
        fun: pw.PyObjectWrapper

    @pw.udf
    def use_python_object(a: pw.PyObjectWrapper, x: str) -> int:
        return a.value(x)

    if data_format == "delta":
        table = pw.io.deltalake.read(auxiliary_path, schema=InputSchema, mode="static")
    elif data_format == "json":
        table = pw.io.jsonlines.read(auxiliary_path, schema=InputSchema, mode="static")
    elif data_format == "csv":
        table = pw.io.csv.read(auxiliary_path, schema=InputSchema, mode="static")
    else:
        raise ValueError(f"Unknown data format: {data_format}")
    table = table.select(len=use_python_object(pw.this.fun, pw.this.data))
    pw.io.jsonlines.write(table, output_path)
    run_all()

    with open(output_path, "r") as f:
        data = json.load(f)
        assert data["len"] == 4