def test_param_repr_ellipsis():
    assert repr(Param(...)) == "Param(PydanticUndefined)"