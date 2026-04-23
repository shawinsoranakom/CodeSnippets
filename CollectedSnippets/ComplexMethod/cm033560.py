def test_add_binary_file(diffs: list[FileDiff]) -> None:
    """Add a binary file."""
    assert len(diffs) == 1

    assert diffs[0].old.exists
    assert diffs[0].new.exists

    assert diffs[0].old.path == 'binary.dat'
    assert diffs[0].new.path == 'binary.dat'

    assert diffs[0].old.eof_newline
    assert diffs[0].new.eof_newline