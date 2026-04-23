def select_command_with_arrows(proc, TIMEOUT):
    """Ensures that command can be selected with arrow keys."""
    _set_confirmation(proc, True)

    proc.sendline(u'git h')
    assert proc.expect([TIMEOUT, u"git: 'h' is not a git command."])

    proc.sendline(u'fuck')
    assert proc.expect([TIMEOUT, u'git show'])
    proc.send('\033[B')
    assert proc.expect([TIMEOUT, u'git push'])
    proc.send('\033[B')
    assert proc.expect([TIMEOUT, u'git help', u'git hook'])
    proc.send('\033[A')
    assert proc.expect([TIMEOUT, u'git push'])
    proc.send('\033[B')
    assert proc.expect([TIMEOUT, u'git help', u'git hook'])
    proc.send('\n')

    assert proc.expect([TIMEOUT, u'usage', u'fatal: not a git repository'])