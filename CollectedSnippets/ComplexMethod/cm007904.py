def test_traversal_expected_type(self):
        _EXPECTED_TYPE_DATA = {'str': 'str', 'int': 0}

        assert traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=str) == 'str', \
            'accept matching `expected_type` type'
        assert traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=int) is None, \
            'reject non matching `expected_type` type'
        # ruff: noqa: PLW0108 `type`s get special treatment, so wrap in lambda
        assert traverse_obj(_EXPECTED_TYPE_DATA, 'int', expected_type=lambda x: str(x)) == '0', \
            'transform type using type function'
        assert traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=lambda _: 1 / 0) is None, \
            'wrap expected_type fuction in try_call'
        assert traverse_obj(_EXPECTED_TYPE_DATA, ..., expected_type=str) == ['str'], \
            'eliminate items that expected_type fails on'
        assert traverse_obj(_TEST_DATA, {0: 100, 1: 1.2}, expected_type=int) == {0: 100}, \
            'type as expected_type should filter dict values'
        assert traverse_obj(_TEST_DATA, {0: 100, 1: 1.2, 2: 'None'}, expected_type=str_or_none) == {0: '100', 1: '1.2'}, \
            'function as expected_type should transform dict values'
        assert traverse_obj(_TEST_DATA, ({0: 1.2}, 0, {int_or_none}), expected_type=int) == 1, \
            'expected_type should not filter non final dict values'
        assert traverse_obj(_TEST_DATA, {0: {0: 100, 1: 'str'}}, expected_type=int) == {0: {0: 100}}, \
            'expected_type should transform deep dict values'
        assert traverse_obj(_TEST_DATA, [({0: '...'}, {0: '...'})], expected_type=type(...)) == [{0: ...}, {0: ...}], \
            'expected_type should transform branched dict values'
        assert traverse_obj({1: {3: 4}}, [(1, 2), 3], expected_type=int) == [4], \
            'expected_type regression for type matching in tuple branching'
        assert traverse_obj(_TEST_DATA, ['data', ...], expected_type=int) == [], \
            'expected_type regression for type matching in dict result'