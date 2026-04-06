def get_new_command(command):
    command_parts = command.script_parts[:]
    index = command_parts.index('rm') + 1
    command_parts.insert(index, '--cached')
    command_list = [u' '.join(command_parts)]
    command_parts[index] = '-f'
    command_list.append(u' '.join(command_parts))
    return command_list