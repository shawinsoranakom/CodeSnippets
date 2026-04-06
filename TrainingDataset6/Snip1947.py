def match(command):
    return command.script_parts[1] == "branch" and first_0flag(command.script_parts)