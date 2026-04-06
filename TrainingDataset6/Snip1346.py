def ifconfig(mocker):
    mock = mocker.patch(
        'thefuck.rules.ifconfig_device_not_found.subprocess.Popen')
    mock.return_value.stdout = BytesIO(stdout)
    return mock