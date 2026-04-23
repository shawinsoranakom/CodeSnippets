def test_traversal_set(self):
        # transformation/type, like `expected_type`
        assert traverse_obj(_TEST_DATA, (..., {str.upper})) == ['STR'], \
            'Function in set should be a transformation'
        assert traverse_obj(_TEST_DATA, (..., {str})) == ['str'], \
            'Type in set should be a type filter'
        assert traverse_obj(_TEST_DATA, (..., {str, int})) == [100, 'str'], \
            'Multiple types in set should be a type filter'
        assert traverse_obj(_TEST_DATA, {dict}) == _TEST_DATA, \
            'A single set should be wrapped into a path'
        assert traverse_obj(_TEST_DATA, (..., {str.upper})) == ['STR'], \
            'Transformation function should not raise'
        expected = [x for x in map(str_or_none, _TEST_DATA.values()) if x is not None]
        assert traverse_obj(_TEST_DATA, (..., {str_or_none})) == expected, \
            'Function in set should be a transformation'
        assert traverse_obj(_TEST_DATA, ('fail', {lambda _: 'const'})) == 'const', \
            'Function in set should always be called'
        # Sets with length < 1 or > 1 not including only types should raise
        with pytest.raises(Exception):
            traverse_obj(_TEST_DATA, set())
        with pytest.raises(Exception):
            traverse_obj(_TEST_DATA, {str.upper, str})