def match(command):
    return (not command.script_parts[0] in get_all_executables()
            and _get_executable(command.script_parts[0]))