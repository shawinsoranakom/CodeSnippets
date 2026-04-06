def proc(request, spawnu, TIMEOUT):
    container, instant_mode = request.param
    proc = spawnu(*container)
    proc.sendline(init_zshrc.format(
        u'--enable-experimental-instant-mode' if instant_mode else ''))
    proc.sendline(u"zsh")
    if instant_mode:
        assert proc.expect([TIMEOUT, u'instant mode ready: True'])
    return proc