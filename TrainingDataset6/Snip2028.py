def get_new_command(command):
    return replace_argument(command.script, 'tag', 'tag --force')