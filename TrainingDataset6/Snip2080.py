def match(command):
    return command.script_parts and 'ls -' not in command.script