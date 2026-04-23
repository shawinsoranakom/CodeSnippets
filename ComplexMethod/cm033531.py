def test_type_hints() -> None:
    """This test isn't really here to test the functionality of to_text/to_bytes
    but more to ensure the overloads are properly validated for type hinting
    """
    d: dict[str, str] = {'k': 'v'}
    s: str = 's'
    b: bytes = b'b'

    to_bytes_bytes: bytes = to_bytes(b)
    to_bytes_str: bytes = to_bytes(s)
    to_bytes_dict: bytes = to_bytes(d)
    assert to_bytes_dict == repr(d).encode('utf-8')

    to_bytes_bytes_repr: bytes = to_bytes(b, nonstring='simplerepr')
    to_bytes_str_repr: bytes = to_bytes(s, nonstring='simplerepr')
    to_bytes_dict_repr: bytes = to_bytes(d, nonstring='simplerepr')
    assert to_bytes_dict_repr == repr(d).encode('utf-8')

    to_bytes_bytes_passthru: bytes = to_bytes(b, nonstring='passthru')
    to_bytes_str_passthru: bytes = to_bytes(s, nonstring='passthru')
    to_bytes_dict_passthru: dict[str, str] = to_bytes(d, nonstring='passthru')
    assert to_bytes_dict_passthru == d

    to_bytes_bytes_empty: bytes = to_bytes(b, nonstring='empty')
    to_bytes_str_empty: bytes = to_bytes(s, nonstring='empty')
    to_bytes_dict_empty: bytes = to_bytes(d, nonstring='empty')
    assert to_bytes_dict_empty == b''

    to_bytes_bytes_strict: bytes = to_bytes(b, nonstring='strict')
    to_bytes_str_strict: bytes = to_bytes(s, nonstring='strict')
    with pytest.raises(TypeError):
        to_bytes_dict_strict: bytes = to_bytes(d, nonstring='strict')

    to_text_bytes: str = to_text(b)
    to_text_str: str = to_text(s)
    to_text_dict: str = to_text(d)
    assert to_text_dict == repr(d)

    to_text_bytes_repr: str = to_text(b, nonstring='simplerepr')
    to_text_str_repr: str = to_text(s, nonstring='simplerepr')
    to_text_dict_repr: str = to_text(d, nonstring='simplerepr')
    assert to_text_dict_repr == repr(d)

    to_text_bytes_passthru: str = to_text(b, nonstring='passthru')
    to_text_str_passthru: str = to_text(s, nonstring='passthru')
    to_text_dict_passthru: dict[str, str] = to_text(d, nonstring='passthru')
    assert to_text_dict_passthru == d

    to_text_bytes_empty: str = to_text(b, nonstring='empty')
    to_text_str_empty: str = to_text(s, nonstring='empty')
    to_text_dict_empty: str = to_text(d, nonstring='empty')
    assert to_text_dict_empty == ''

    to_text_bytes_strict: str = to_text(b, nonstring='strict')
    to_text_str_strict: str = to_text(s, nonstring='strict')
    with pytest.raises(TypeError):
        to_text_dict_strict: str = to_text(d, nonstring='strict')