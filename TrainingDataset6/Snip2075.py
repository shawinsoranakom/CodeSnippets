def get_new_command(command):
    destination = _get_destination(command.script_parts)
    parts = command.script_parts[:]
    parts.remove(destination)
    parts.append(destination)
    return ' '.join(parts)