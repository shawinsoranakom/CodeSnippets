def get_new_command(command):
    closest_subcommand = get_closest(command.script_parts[1], get_golang_commands())
    return replace_argument(command.script, command.script_parts[1],
                            closest_subcommand)