def grunt_help(mocker):
    patch = mocker.patch('thefuck.rules.grunt_task_not_found.Popen')
    patch.return_value.stdout = BytesIO(grunt_help_stdout)
    return patch