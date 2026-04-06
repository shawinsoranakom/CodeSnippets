def match(command):
    return (command.script_parts[1] == 'help'
            and 'for documentation about this command.' in command.output)