def test_key_comparison() -> None:
    """Test key comparison with itself and string keys."""

    str_key = "custom-key"
    key = HassKey[int](str_key)
    other_key = HassKey[str]("other-key")

    entry_key = HassEntryKey[int](str_key)
    other_entry_key = HassEntryKey[str]("other-key")

    assert key == str_key
    assert key != other_key
    assert key != 2

    assert entry_key == str_key
    assert entry_key != other_entry_key
    assert entry_key != 2

    # Only compare name attribute, HassKey(<name>) == HassEntryKey(<name>)
    assert key == entry_key