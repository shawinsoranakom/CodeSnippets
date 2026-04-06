def history(mocker):
    return mocker.patch(
        'thefuck.rules.path_from_history.get_valid_history_without_current',
        return_value=['cd /opt/java', 'ls ~/work/project/'])