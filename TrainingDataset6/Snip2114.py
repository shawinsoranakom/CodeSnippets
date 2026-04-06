def get_new_command(command):
    npm_commands = _get_available_commands(command.output)
    wrong_command = _get_wrong_command(command.script_parts)
    fixed = get_closest(wrong_command, npm_commands)
    return replace_argument(command.script, wrong_command, fixed)