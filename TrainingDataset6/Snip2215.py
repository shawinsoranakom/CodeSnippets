def match(command):
    first_part = command.script_parts[0]
    if "-" not in first_part or first_part in get_all_executables():
        return False
    cmd, _ = first_part.split("-", 1)
    return cmd in get_all_executables()