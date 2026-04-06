def get_new_command(command):
    return shell.and_('git add --update', 'git stash pop', 'git reset .')