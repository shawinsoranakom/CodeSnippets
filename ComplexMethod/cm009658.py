def test_known_block_types() -> None:
    expected = {
        bt
        for bt in get_args(ContentBlock)
        for bt in get_args(bt.__annotations__["type"])
    }
    # Normalize any Literal[...] types in block types to their string values.
    # This ensures all entries are plain strings, not Literal objects.
    expected = {
        t
        if isinstance(t, str)
        else t.__args__[0]
        if hasattr(t, "__args__") and len(t.__args__) == 1
        else t
        for t in expected
    }
    assert expected == KNOWN_BLOCK_TYPES