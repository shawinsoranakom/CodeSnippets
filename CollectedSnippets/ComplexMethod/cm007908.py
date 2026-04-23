def test_traversal_unbranching(self):
        assert traverse_obj(_TEST_DATA, [(100, 1.2), all]) == [100, 1.2], \
            '`all` should give all results as list'
        assert traverse_obj(_TEST_DATA, [(100, 1.2), any]) == 100, \
            '`any` should give the first result'
        assert traverse_obj(_TEST_DATA, [100, all]) == [100], \
            '`all` should give list if non branching'
        assert traverse_obj(_TEST_DATA, [100, any]) == 100, \
            '`any` should give single item if non branching'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 100), all]) == [100], \
            '`all` should filter `None` and empty dict'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 100), any]) == 100, \
            '`any` should filter `None` and empty dict'
        assert traverse_obj(_TEST_DATA, [{
            'all': [('dict', 'None', 100, 1.2), all],
            'any': [('dict', 'None', 100, 1.2), any],
        }]) == {'all': [100, 1.2], 'any': 100}, \
            '`all`/`any` should apply to each dict path separately'
        assert traverse_obj(_TEST_DATA, [{
            'all': [('dict', 'None', 100, 1.2), all],
            'any': [('dict', 'None', 100, 1.2), any],
        }], get_all=False) == {'all': [100, 1.2], 'any': 100}, \
            '`all`/`any` should apply to dict regardless of `get_all`'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), all, {float}]) is None, \
            '`all` should reset branching status'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), any, {float}]) is None, \
            '`any` should reset branching status'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 100, 1.2), all, ..., {float}]) == [1.2], \
            '`all` should allow further branching'
        assert traverse_obj(_TEST_DATA, [('dict', 'None', 'urls', 'data'), any, ..., 'index']) == [0, 1], \
            '`any` should allow further branching'