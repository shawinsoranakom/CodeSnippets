def all_executables(mocker):
    return mocker.patch(
        'thefuck.rules.missing_space_before_subcommand.get_all_executables',
        return_value=['git', 'ls', 'npm', 'w', 'watch'])