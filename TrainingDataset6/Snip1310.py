def tasks(mocker):
    patch = mocker.patch('thefuck.rules.gradle_no_task.Popen')
    patch.return_value.stdout = BytesIO(gradle_tasks)
    return patch