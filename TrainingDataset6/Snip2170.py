def get_new_command(command):
    script = shlex.split(command.script)

    for (i, e) in enumerate(script):
        if e.startswith(('s/', '-es/')) and e[-1] != '/':
            script[i] += '/'

    return ' '.join(map(shell.quote, script))