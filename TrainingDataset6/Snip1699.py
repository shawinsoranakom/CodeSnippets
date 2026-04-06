def test_from_script_calls(self, Popen, settings, os_environ):
        settings.env = {}
        assert Command.from_raw_script(
            ['apt-get', 'search', 'vim']) == Command(
            'apt-get search vim', 'output')
        Popen.assert_called_once_with('apt-get search vim',
                                      shell=True,
                                      stdin=PIPE,
                                      stdout=PIPE,
                                      stderr=STDOUT,
                                      env=os_environ)