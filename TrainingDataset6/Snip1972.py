def match(command):
    return ('diff' in command.script and
            '--staged' not in command.script)