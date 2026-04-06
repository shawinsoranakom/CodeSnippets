def match(command):
    return (
        'NOTESTS' in command.output
        and not any(_is_recursive(part) for part in command.script_parts[1:])
        and any(_isdir(part) for part in command.script_parts[1:]))