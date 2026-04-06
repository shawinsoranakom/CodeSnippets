def test_app_alias_alter_history(self, settings, shell):
        settings.alter_history = True
        assert (
            'builtin history delete --exact --case-sensitive -- $fucked_up_command\n'
            in shell.app_alias('FUCK')
        )
        assert 'builtin history merge\n' in shell.app_alias('FUCK')
        settings.alter_history = False
        assert 'builtin history delete' not in shell.app_alias('FUCK')
        assert 'builtin history merge' not in shell.app_alias('FUCK')