def test_get_types() -> None:
    assert get_types(Union[int, str]) == (int, str)
    assert get_types(int | str) == (int, str)
    assert get_types(int) == (int,)
    assert get_types(str) == (str,)
    assert get_types("test") is None
    assert get_types(Optional[int]) == (int, NoneType)
    assert get_types(NoneType) == (NoneType,)
    assert get_types(None) == (NoneType,)