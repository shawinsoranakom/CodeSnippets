def match(command):
    return len(get_close_matches(command.script,
                                 get_valid_history_without_current(command)))