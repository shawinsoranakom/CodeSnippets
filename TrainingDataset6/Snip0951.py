def history_changed(proc, TIMEOUT, *to):
    """Ensures that history changed."""
    proc.send('\033[A')
    pattern = [TIMEOUT]
    pattern.extend(to)
    assert proc.expect(pattern)