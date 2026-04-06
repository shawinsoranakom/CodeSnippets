def get_new_command(command):
    return ' '.join(['ls', '-A'] + command.script_parts[1:])