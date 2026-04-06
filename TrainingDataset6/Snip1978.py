def match(command):
    return 'help' in command.script and ' is aliased to ' in command.output