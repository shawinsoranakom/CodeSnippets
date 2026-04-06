def get_new_command(command):
    to = command.output.split('`')[1]
    return replace_argument(command.script, to[1:], to)