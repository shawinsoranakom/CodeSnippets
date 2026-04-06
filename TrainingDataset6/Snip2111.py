def _get_wrong_command(script_parts):
    commands = [part for part in script_parts[1:] if not part.startswith('-')]
    if commands:
        return commands[0]