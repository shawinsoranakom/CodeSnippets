def history_not_changed(proc, TIMEOUT):
    """Ensures that history not changed."""
    proc.send('\033[A')
    assert proc.expect([TIMEOUT, u'fuck'])