def _get_executable(script_part):
    for executable in get_all_executables():
        if len(executable) > 1 and script_part.startswith(executable):
            return executable