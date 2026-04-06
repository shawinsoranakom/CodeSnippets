def test_app_alias(self, shell):
        assert 'setenv TF_SHELL tcsh' in shell.app_alias('fuck')
        assert 'alias fuck' in shell.app_alias('fuck')
        assert 'alias FUCK' in shell.app_alias('FUCK')
        assert 'thefuck' in shell.app_alias('fuck')