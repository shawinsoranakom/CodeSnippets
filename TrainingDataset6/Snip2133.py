def match(command):
    return ('pip install' in command.script and 'Permission denied' in command.output)