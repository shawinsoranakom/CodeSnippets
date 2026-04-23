def test_traversal_default(self):
        _DEFAULT_DATA = {'None': None, 'int': 0, 'list': []}

        assert traverse_obj(_DEFAULT_DATA, 'fail') is None, \
            'default value should be `None`'
        assert traverse_obj(_DEFAULT_DATA, 'fail', 'fail', default=...) == ..., \
            'chained fails should result in default'
        assert traverse_obj(_DEFAULT_DATA, 'None', 'int') == 0, \
            'should not short cirquit on `None`'
        assert traverse_obj(_DEFAULT_DATA, 'fail', default=1) == 1, \
            'invalid dict key should result in `default`'
        assert traverse_obj(_DEFAULT_DATA, 'None', default=1) == 1, \
            '`None` is a deliberate sentinel and should become `default`'
        assert traverse_obj(_DEFAULT_DATA, ('list', 10)) is None, \
            '`IndexError` should result in `default`'
        assert traverse_obj(_DEFAULT_DATA, (..., 'fail'), default=1) == 1, \
            'if branched but not successful return `default` if defined, not `[]`'
        assert traverse_obj(_DEFAULT_DATA, (..., 'fail'), default=None) is None, \
            'if branched but not successful return `default` even if `default` is `None`'
        assert traverse_obj(_DEFAULT_DATA, (..., 'fail')) == [], \
            'if branched but not successful return `[]`, not `default`'
        assert traverse_obj(_DEFAULT_DATA, ('list', ...)) == [], \
            'if branched but object is empty return `[]`, not `default`'
        assert traverse_obj(None, ...) == [], \
            'if branched but object is `None` return `[]`, not `default`'
        assert traverse_obj({0: None}, (0, ...)) == [], \
            'if branched but state is `None` return `[]`, not `default`'