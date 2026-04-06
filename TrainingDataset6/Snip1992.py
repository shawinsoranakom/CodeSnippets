def match(command):
    return 'pull' in command.script and 'set-upstream' in command.output