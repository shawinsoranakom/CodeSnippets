def test_header_repr_ellipsis():
    assert repr(Header(...)) == "Header(PydanticUndefined)"