def test_and_(self, shell):
        assert shell.and_('ls', 'cd') == '(ls) -and (cd)'