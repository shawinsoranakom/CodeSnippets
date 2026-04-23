def test_schema_eq():
    class A(pw.Schema):
        a: int = pw.column_definition(primary_key=True)
        b: str = pw.column_definition(default_value="foo")

    class B(pw.Schema):
        b: str = pw.column_definition(default_value="foo")
        a: int = pw.column_definition(primary_key=True)

    class C(pw.Schema):
        a: int = pw.column_definition(primary_key=True)
        b: str = pw.column_definition(default_value="foo")
        c: int

    class D(pw.Schema):
        a: int = pw.column_definition()
        b: str = pw.column_definition(default_value="foo")

    class E(pw.Schema):
        a: str = pw.column_definition(primary_key=True)
        b: str = pw.column_definition(default_value="foo")

    class F(pw.Schema, append_only=True):
        a: int = pw.column_definition(primary_key=True)
        b: str = pw.column_definition(default_value="foo")

    class Same(pw.Schema):
        a: int = pw.column_definition(primary_key=True)
        b: str = pw.column_definition(default_value="foo")

    schema_from_builder = pw.schema_builder(
        columns={
            "a": pw.column_definition(primary_key=True, dtype=int),
            "b": pw.column_definition(default_value="foo", dtype=str),
        },
        name="Foo",
    )

    assert A != B, "column order should match"
    assert A != C, "column count should match"
    assert A != D, "column properties should match"
    assert A != E, "column types should match"
    assert A != F, "schema properties should match"
    assert A == Same
    assert A == schema_from_builder