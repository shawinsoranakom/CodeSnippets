def get_new_command(command):
    return get_closest(command.script,
                       get_valid_history_without_current(command))