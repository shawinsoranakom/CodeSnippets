def match(command):
    if 'command not found' in command.output:
        command_name = _get_command_name(command)
        return which(command_name)