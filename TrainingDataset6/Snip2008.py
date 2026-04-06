def get_new_command(command):
    return shell.and_('git commit -m "Initial commit"', command.script)