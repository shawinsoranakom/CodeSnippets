def match(command):
    return command.script_parts and os.path.exists(command.script_parts[0]) \
        and 'command not found' in command.output