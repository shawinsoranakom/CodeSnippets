def get_new_command(command):
    return shell.and_('tsuru login', command.script)