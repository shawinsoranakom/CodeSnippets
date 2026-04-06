def _get_executable(command):
    if command.script_parts[0] == 'sudo':
        return command.script_parts[1]
    else:
        return command.script_parts[0]