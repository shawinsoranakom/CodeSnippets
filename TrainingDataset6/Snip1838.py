def get_new_command(command):
    invalid_operation = command.output.split()[-1]

    if invalid_operation == 'uninstall':
        return [command.script.replace('uninstall', 'remove')]

    else:
        operations = _get_operations(command.script_parts[0])
        return replace_command(command, invalid_operation, operations)