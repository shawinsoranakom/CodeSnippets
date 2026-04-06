def get_new_command(command):
    return shell.and_(u"mkdir -p {}".format(command.script_parts[-1]), command.script)