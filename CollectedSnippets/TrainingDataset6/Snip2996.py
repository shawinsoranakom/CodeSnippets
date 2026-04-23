def test_body_repr_ellipsis():
    assert repr(Body(...)) == "Body(PydanticUndefined)"