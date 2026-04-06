def get_new_command(command):
    return shell.and_('git branch --delete list', 'git branch')