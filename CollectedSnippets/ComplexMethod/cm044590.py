def test_is_single_cell_widths() -> None:
    # Check _is_single_cell_widths reports correctly
    for character in string.printable:
        if ord(character) >= 32:
            assert _is_single_cell_widths(character)

    BOX = "┌─┬┐│ ││├─┼┤│ ││├─┼┤├─┼┤│ ││└─┴┘"

    for character in BOX:
        assert _is_single_cell_widths(character)

    for character in "💩😽":
        assert not _is_single_cell_widths(character)

    for character in "わさび":
        assert not _is_single_cell_widths(character)