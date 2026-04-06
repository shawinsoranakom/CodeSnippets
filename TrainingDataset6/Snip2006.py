def get_new_command(command):
    return shell.and_(replace_argument(command.script, 'push', 'pull'),
                      command.script)