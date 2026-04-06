def gem_help_commands(mocker):
    patch = mocker.patch('subprocess.Popen')
    patch.return_value.stdout = BytesIO(gem_help_commands_stdout)
    return patch