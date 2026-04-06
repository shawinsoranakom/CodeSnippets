def test_how_to_configure_alias(proc, TIMEOUT):
    proc.sendline(u'unfunction fuck')
    how_to_configure(proc, TIMEOUT)