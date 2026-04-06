def get_new_command(command):
    aliased = command.output.split('`', 2)[2].split("'", 1)[0].split(' ', 1)[0]
    return 'git help {}'.format(aliased)