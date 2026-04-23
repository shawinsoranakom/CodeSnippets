def test_remove_trailing_newline(diffs: list[FileDiff]) -> None:
    """Remove the trailing newline from a file."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert not diffs[0].new.eof_newline