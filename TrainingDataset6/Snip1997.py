def get_new_command(command):
    return shell.and_('git stash', 'git pull', 'git stash pop')