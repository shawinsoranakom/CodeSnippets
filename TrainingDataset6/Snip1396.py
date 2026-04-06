def history_without_current(mocker):
    return mocker.patch(
        'thefuck.rules.no_command.get_valid_history_without_current',
        return_value=['git commit'])