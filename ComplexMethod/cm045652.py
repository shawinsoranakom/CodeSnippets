def test_schema_properties():
    class A(pw.Schema, append_only=True):
        a: int = pw.column_definition(append_only=True)
        b: int = pw.column_definition()

    assert A["a"].append_only is True
    assert A["b"].append_only is True
    assert A.universe_properties.append_only is True

    class B(pw.Schema, append_only=False):
        a: int = pw.column_definition(append_only=False)
        b: int = pw.column_definition()

    assert B["a"].append_only is False
    assert B["b"].append_only is False
    assert B.universe_properties.append_only is False

    class C(pw.Schema):
        a: int = pw.column_definition(append_only=True)
        b: int = pw.column_definition(append_only=False)
        c: int = pw.column_definition()

    assert C["a"].append_only is True
    assert C["b"].append_only is False
    assert C["c"].append_only is False
    assert C.universe_properties.append_only is True

    class D(pw.Schema, append_only=True):
        pass

    assert D.universe_properties.append_only is True