def test_or_(self, shell):
        assert shell.or_('ls', 'cd') == 'ls || cd'