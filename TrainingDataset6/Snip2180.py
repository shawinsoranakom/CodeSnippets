def get_new_command(command):
    command_name = _get_command_name(command)
    return replace_argument(command.script, command_name,
                            u'env "PATH=$PATH" {}'.format(command_name))