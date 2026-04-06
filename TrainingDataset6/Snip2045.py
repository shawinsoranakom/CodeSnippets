def get_new_command(command):
    return u'grep -r {}'.format(command.script[5:])