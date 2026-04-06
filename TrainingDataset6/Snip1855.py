def get_new_command(command):
    command_parts = command.script_parts[:]
    command_parts[1] = 'link'
    command_parts.insert(2, '--overwrite')
    command_parts.insert(3, '--dry-run')
    return ' '.join(command_parts)