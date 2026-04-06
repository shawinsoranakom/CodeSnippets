def history_without_current(mocker):
    return mocker.patch(
        'thefuck.rules.history.get_valid_history_without_current',
        return_value=['ls cat', 'diff x'])