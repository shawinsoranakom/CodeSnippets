def match(command):
    return ('add' in command.script_parts
            and 'Use -f if you really want to add them.' in command.output)