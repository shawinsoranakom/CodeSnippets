def test_or_(self, shell):
        assert shell.or_('foo', 'bar') == 'foo; or bar'