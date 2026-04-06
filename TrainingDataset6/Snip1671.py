def test_from_env_with_DEFAULT(self, os_environ, settings):
        os_environ.update({'THEFUCK_RULES': 'DEFAULT_RULES:bash:lisp'})
        settings.init()
        assert settings.rules == const.DEFAULT_RULES + ['bash', 'lisp']