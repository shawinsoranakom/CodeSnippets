def test_from_env(self, os_environ, settings):
        os_environ.update({'THEFUCK_RULES': 'bash:lisp',
                           'THEFUCK_EXCLUDE_RULES': 'git:vim',
                           'THEFUCK_WAIT_COMMAND': '55',
                           'THEFUCK_REQUIRE_CONFIRMATION': 'true',
                           'THEFUCK_NO_COLORS': 'false',
                           'THEFUCK_PRIORITY': 'bash=10:lisp=wrong:vim=15',
                           'THEFUCK_WAIT_SLOW_COMMAND': '999',
                           'THEFUCK_SLOW_COMMANDS': 'lein:react-native:./gradlew',
                           'THEFUCK_NUM_CLOSE_MATCHES': '359',
                           'THEFUCK_EXCLUDED_SEARCH_PATH_PREFIXES': '/media/:/mnt/'})
        settings.init()
        assert settings.rules == ['bash', 'lisp']
        assert settings.exclude_rules == ['git', 'vim']
        assert settings.wait_command == 55
        assert settings.require_confirmation is True
        assert settings.no_colors is False
        assert settings.priority == {'bash': 10, 'vim': 15}
        assert settings.wait_slow_command == 999
        assert settings.slow_commands == ['lein', 'react-native', './gradlew']
        assert settings.num_close_matches == 359
        assert settings.excluded_search_path_prefixes == ['/media/', '/mnt/']