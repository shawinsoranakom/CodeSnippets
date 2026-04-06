def get_new_command(command):
    return u'{} --delete-ghost-migrations'.format(command.script)