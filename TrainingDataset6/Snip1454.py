def lsof(mocker):
    patch = mocker.patch('thefuck.rules.port_already_in_use.Popen')
    patch.return_value.stdout = BytesIO(lsof_stdout)
    return patch