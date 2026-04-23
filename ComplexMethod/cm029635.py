def win_getpass(prompt='Password: ', stream=None, *, echo_char=None):
    """Prompt for password with echo off, using Windows getwch()."""
    if sys.stdin is not sys.__stdin__:
        return fallback_getpass(prompt, stream)
    _check_echo_char(echo_char)

    for c in prompt:
        msvcrt.putwch(c)
    pw = ""
    while 1:
        c = msvcrt.getwch()
        if c == '\r' or c == '\n':
            break
        if c == '\003':
            raise KeyboardInterrupt
        if c == '\b':
            if echo_char and pw:
                msvcrt.putwch('\b')
                msvcrt.putwch(' ')
                msvcrt.putwch('\b')
            pw = pw[:-1]
        else:
            pw = pw + c
            if echo_char:
                msvcrt.putwch(echo_char)
    msvcrt.putwch('\r')
    msvcrt.putwch('\n')
    return pw