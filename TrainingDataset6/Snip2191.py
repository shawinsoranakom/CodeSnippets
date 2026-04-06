def get_new_command(command):
    return shell.and_('terraform init', command.script)