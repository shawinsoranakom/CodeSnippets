def test_and_(self, shell):
        assert shell.and_('foo', 'bar') == 'foo; and bar'