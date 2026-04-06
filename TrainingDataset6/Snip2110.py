def get_new_command(command):
    parts = command.script_parts[:]
    parts.insert(1, 'run-script')
    return ' '.join(parts)