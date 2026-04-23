def test_cookie_repr_ellipsis():
    assert repr(Cookie(...)) == "Cookie(PydanticUndefined)"