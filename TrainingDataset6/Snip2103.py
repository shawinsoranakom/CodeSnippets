def _get_used_executables(command):
    for script in get_valid_history_without_current(command):
        yield script.split(' ')[0]