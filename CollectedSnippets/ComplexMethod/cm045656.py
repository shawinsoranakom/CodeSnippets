def test_dtypes():
    py_object_int = pw.PyObjectWrapper(10)
    assert dt.wrap(pw.PyObjectWrapper[int]).is_value_compatible(py_object_int)
    assert dt.wrap(pw.PyObjectWrapper).is_value_compatible(py_object_int)
    assert not dt.wrap(pw.PyObjectWrapper[str]).is_value_compatible(py_object_int)

    @dataclass
    class Simple:
        b: bytes

    py_object_simple = pw.PyObjectWrapper(Simple("abc".encode()))
    assert dt.wrap(pw.PyObjectWrapper[Simple]).is_value_compatible(py_object_simple)
    assert dt.wrap(pw.PyObjectWrapper).is_value_compatible(py_object_simple)
    assert not dt.wrap(pw.PyObjectWrapper[bytes]).is_value_compatible(py_object_simple)
    assert not dt.wrap(pw.PyObjectWrapper[int]).is_value_compatible(py_object_simple)