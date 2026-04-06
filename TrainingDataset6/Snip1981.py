def get_new_command(command):
    hooked_command = next(
        hooked_command
        for hooked_command in hooked_commands
        if hooked_command in command.script_parts
    )
    return replace_argument(
        command.script, hooked_command, hooked_command + " --no-verify"
    )