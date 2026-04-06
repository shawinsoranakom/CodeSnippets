def get_new_command(command):
    formatme = shell.and_('git stash', '{}')
    return formatme.format(command.script)