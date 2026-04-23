def test_traversal_base(self):
        assert traverse_obj(_TEST_DATA, ('str',)) == 'str', \
            'allow tuple path'
        assert traverse_obj(_TEST_DATA, ['str']) == 'str', \
            'allow list path'
        assert traverse_obj(_TEST_DATA, (value for value in ('str',))) == 'str', \
            'allow iterable path'
        assert traverse_obj(_TEST_DATA, 'str') == 'str', \
            'single items should be treated as a path'
        assert traverse_obj(_TEST_DATA, 100) == 100, \
            'allow int path'
        assert traverse_obj(_TEST_DATA, 1.2) == 1.2, \
            'allow float path'
        assert traverse_obj(_TEST_DATA, None) == _TEST_DATA, \
            '`None` should not perform any modification'