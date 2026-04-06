def match(command):
    if command.script_parts and len(command.script_parts) > 1:
        return (command.script_parts[1] == 'stash'
                and 'usage:' in command.output)
    else:
        return False