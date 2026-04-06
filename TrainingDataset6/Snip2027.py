def match(command):
    return ('tag' in command.script_parts
            and 'already exists' in command.output)