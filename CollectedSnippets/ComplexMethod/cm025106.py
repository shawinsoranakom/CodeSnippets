async def test_result_wrappers(hass: HomeAssistant) -> None:
    """Test result wrappers."""
    for text, native, orig_type, schema in (
        ("[1, 2]", [1, 2], list, vol.Schema([int])),
        ("{1, 2}", {1, 2}, set, vol.Schema({int})),
        ("(1, 2)", (1, 2), tuple, vol.ExactSequence([int, int])),
        ('{"hello": True}', {"hello": True}, dict, vol.Schema({"hello": bool})),
    ):
        result = render(hass, text)
        assert isinstance(result, orig_type)
        assert isinstance(result, template.ResultWrapper)
        assert result == native
        assert result.render_result == text
        schema(result)  # should not raise
        # Result with render text stringifies to original text
        assert str(result) == text
        # Result without render text stringifies same as original type
        assert str(template.RESULT_WRAPPERS[orig_type](native)) == str(
            orig_type(native)
        )