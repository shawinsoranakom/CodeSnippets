def test_escape():
    # Potential tags
    assert escape("foo[bar]") == r"foo\[bar]"
    assert escape(r"foo\[bar]") == r"foo\\\[bar]"

    # Not tags (escape not required)
    assert escape("[5]") == "[5]"
    assert escape("\\[5]") == "\\[5]"

    # Test @ escape
    assert escape("[@foo]") == "\\[@foo]"
    assert escape("[@]") == "\\[@]"

    # https://github.com/Textualize/rich/issues/2187
    assert escape("[nil, [nil]]") == r"[nil, \[nil]]"