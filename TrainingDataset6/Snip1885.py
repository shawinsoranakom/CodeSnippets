def get_new_command(command):
    return shell.and_(
        'chmod +x {}'.format(command.script_parts[0][2:]),
        command.script)