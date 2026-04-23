def test_add_text_file(diffs: list[FileDiff]) -> None:
    """Add a new file."""
    assert len(diffs) == 1

    assert not diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline