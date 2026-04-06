def yarn_help(mocker):
    patch = mocker.patch('thefuck.rules.yarn_command_not_found.Popen')
    patch.return_value.stdout = BytesIO(yarn_help_stdout)
    return patch