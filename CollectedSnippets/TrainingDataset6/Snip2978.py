def test_path_repr():
    assert repr(Path()) == "Path(PydanticUndefined)"
    assert repr(Path(...)) == "Path(PydanticUndefined)"