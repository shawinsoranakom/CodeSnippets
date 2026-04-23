def test_unpack(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Test struct unpack method."""

    variables = {"value": b"\xde\xad\xbe\xef"}

    # render as filter
    result = render(hass, """{{ value | unpack('>I') }}""", variables)
    assert result == 0xDEADBEEF

    # render as function
    result = render(hass, """{{ unpack(value, '>I') }}""", variables)
    assert result == 0xDEADBEEF

    # unpack with offset
    result = render(hass, """{{ unpack(value, '>H', offset=2) }}""", variables)
    assert result == 0xBEEF

    # test with an empty bytes object
    assert render(hass, """{{ unpack(value, '>I') }}""", {"value": b""}) is None
    assert (
        "Template warning: 'unpack' unable to unpack object 'b''' with format_string"
        " '>I' and offset 0 see https://docs.python.org/3/library/struct.html for more"
        " information" in caplog.text
    )

    # test with invalid filter
    assert (
        render(hass, """{{ unpack(value, 'invalid filter') }}""", {"value": b""})
        is None
    )
    assert (
        "Template warning: 'unpack' unable to unpack object 'b''' with format_string"
        " 'invalid filter' and offset 0 see"
        " https://docs.python.org/3/library/struct.html for more information"
        in caplog.text
    )