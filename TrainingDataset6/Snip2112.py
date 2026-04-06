def match(command):
    return (command.script_parts[0] == 'npm' and
            'where <command> is one of:' in command.output and
            _get_wrong_command(command.script_parts))