def test_add_two_text_files(diffs: list[FileDiff]) -> None:
    """Add two text files."""
    assert len(diffs) == 2

    assert not diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'one.txt'
    assert diffs[0].new.path == 'one.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline

    assert not diffs[1].old.exists
    assert diffs[1].new.exists

    assert diffs[1].old.path == 'two.txt'
    assert diffs[1].new.path == 'two.txt'

    assert diffs[1].old.eof_newline
    assert diffs[1].new.eof_newline