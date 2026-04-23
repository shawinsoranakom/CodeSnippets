def test_traversal_dict(self):
        assert traverse_obj(_TEST_DATA, {0: 100, 1: 1.2}) == {0: 100, 1: 1.2}, \
            'dict key should result in a dict with the same keys'
        expected = {0: 'https://www.example.com/0'}
        assert traverse_obj(_TEST_DATA, {0: ('urls', 0, 'url')}) == expected, \
            'dict key should allow paths'
        expected = {0: ['https://www.example.com/0']}
        assert traverse_obj(_TEST_DATA, {0: ('urls', (3, 0), 'url')}) == expected, \
            'tuple in dict path should be treated as branches'
        assert traverse_obj(_TEST_DATA, {0: ('urls', ((1, 'fail'), (0, 'url')))}) == expected, \
            'double nesting in dict path should be treated as paths'
        expected = {0: ['https://www.example.com/1', 'https://www.example.com/0']}
        assert traverse_obj(_TEST_DATA, {0: ('urls', ((1, ('fail', 'url')), (0, 'url')))}) == expected, \
            'tripple nesting in dict path should be treated as branches'
        assert traverse_obj(_TEST_DATA, {0: 'fail'}) == {}, \
            'remove `None` values when top level dict key fails'
        assert traverse_obj(_TEST_DATA, {0: 'fail'}, default=...) == {0: ...}, \
            'use `default` if key fails and `default`'
        assert traverse_obj(_TEST_DATA, {0: 'dict'}) == {}, \
            'remove empty values when dict key'
        assert traverse_obj(_TEST_DATA, {0: 'dict'}, default=...) == {0: ...}, \
            'use `default` when dict key and `default`'
        assert traverse_obj(_TEST_DATA, {0: {0: 'fail'}}) == {}, \
            'remove empty values when nested dict key fails'
        assert traverse_obj(None, {0: 'fail'}) == {}, \
            'default to dict if pruned'
        assert traverse_obj(None, {0: 'fail'}, default=...) == {0: ...}, \
            'default to dict if pruned and default is given'
        assert traverse_obj(_TEST_DATA, {0: {0: 'fail'}}, default=...) == {0: {0: ...}}, \
            'use nested `default` when nested dict key fails and `default`'
        assert traverse_obj(_TEST_DATA, {0: ('dict', ...)}) == {}, \
            'remove key if branch in dict key not successful'