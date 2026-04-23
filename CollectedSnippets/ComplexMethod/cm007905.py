def test_traversal_traverse_string(self):
        _TRAVERSE_STRING_DATA = {'str': 'str', 1.2: 1.2}

        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0)) is None, \
            'do not traverse into string if not `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0), traverse_string=True) == 's', \
            'traverse into string if `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, (1.2, 1), traverse_string=True) == '.', \
            'traverse into converted data if `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', ...), traverse_string=True) == 'str', \
            '`...` should result in string (same value) if `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', slice(0, None, 2)), traverse_string=True) == 'sr', \
            '`slice` should result in string if `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', lambda i, v: i or v == 's'), traverse_string=True) == 'str', \
            'function should result in string if `traverse_string`'
        assert traverse_obj(_TRAVERSE_STRING_DATA, ('str', (0, 2)), traverse_string=True) == ['s', 'r'], \
            'branching should result in list if `traverse_string`'
        assert traverse_obj({}, (0, ...), traverse_string=True) == [], \
            'branching should result in list if `traverse_string`'
        assert traverse_obj({}, (0, lambda x, y: True), traverse_string=True) == [], \
            'branching should result in list if `traverse_string`'
        assert traverse_obj({}, (0, slice(1)), traverse_string=True) == [], \
            'branching should result in list if `traverse_string`'