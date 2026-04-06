def _set_confirmation(proc, require):
    proc.sendline(u'mkdir -p ~/.thefuck')
    proc.sendline(
        u'echo "require_confirmation = {}" > ~/.thefuck/settings.py'.format(
            require))