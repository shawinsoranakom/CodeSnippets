def get_new_command(command):
    return shell.and_('docker login', command.script)