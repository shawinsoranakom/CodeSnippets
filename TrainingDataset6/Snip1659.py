def test_get_scripts(mocker):
    patch = mocker.patch('thefuck.specific.npm.Popen')
    patch.return_value.stdout = BytesIO(run_script_stdout)
    assert get_scripts() == ['build', 'develop', 'watch-test']