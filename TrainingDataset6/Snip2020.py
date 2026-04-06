def get_new_command(command):
    command_parts = command.script_parts[:]
    index = command_parts.index('rm') + 1
    command_parts.insert(index, '-r')
    return u' '.join(command_parts)