def match(command):
    return (len(command.script_parts) >= 2
            and command.script_parts[1] not in _get_all_environments())