def get_new_command(command):
    command_parts = command.script_parts[:]
    command_parts[1] = 'uninstall'
    command_parts.insert(2, '--force')
    return ' '.join(command_parts)