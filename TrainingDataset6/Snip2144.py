def get_new_command(command):
    parts = command.script_parts[:]
    parts.insert(1, '-r')
    return u' '.join(parts)