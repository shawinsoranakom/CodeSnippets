def get_new_command(command):
    invalid_operation = command.script_parts[1]

    if invalid_operation == 'uninstall':
        return [command.script.replace('uninstall', 'remove')]

    return replace_command(command, invalid_operation, _get_operations())