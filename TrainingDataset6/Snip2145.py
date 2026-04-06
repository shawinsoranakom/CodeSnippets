def match(command):
    return (command.script_parts
            and command.script_parts[0].endswith('.py')
            and ('Permission denied' in command.output or
                 'command not found' in command.output))