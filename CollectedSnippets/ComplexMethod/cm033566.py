def test_multiple_context_lines(diffs: list[FileDiff]) -> None:
    """Multiple context lines."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'test.txt'
    assert diffs[0].new.path == 'test.txt'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline