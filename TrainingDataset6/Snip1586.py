def test_app_alias_variables_correctly_set(self, shell):
        alias = shell.app_alias('fuck')
        assert "fuck () {" in alias
        assert 'TF_SHELL=bash' in alias
        assert "TF_ALIAS=fuck" in alias
        assert 'PYTHONIOENCODING=utf-8' in alias
        assert 'TF_SHELL_ALIASES=$(alias)' in alias