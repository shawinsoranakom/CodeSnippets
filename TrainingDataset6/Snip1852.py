def match(command):
    is_proper_command = ('install' in command.script and
                         'No available formula' in command.output and
                         'Did you mean' in command.output)
    return is_proper_command