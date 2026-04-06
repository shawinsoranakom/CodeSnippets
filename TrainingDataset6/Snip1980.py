def match(command):
    return any(
        hooked_command in command.script_parts for hooked_command in hooked_commands
    )