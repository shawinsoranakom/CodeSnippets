def get_new_command(command):
    actual_file = _get_actual_file(command.script_parts)
    parts = command.script_parts[::]
    # Moves file to the end of the script:
    parts.remove(actual_file)
    parts.append(actual_file)
    return ' '.join(parts)