def test_dict_get(self):
        FALSE_VALUES = {
            'none': None,
            'false': False,
            'zero': 0,
            'empty_string': '',
            'empty_list': [],
        }
        d = {**FALSE_VALUES, 'a': 42}
        assert dict_get(d, 'a') == 42
        assert dict_get(d, 'b') is None
        assert dict_get(d, 'b', 42) == 42
        assert dict_get(d, ('a',)) == 42
        assert dict_get(d, ('b', 'a')) == 42
        assert dict_get(d, ('b', 'c', 'a', 'd')) == 42
        assert dict_get(d, ('b', 'c')) is None
        assert dict_get(d, ('b', 'c'), 42) == 42
        for key, false_value in FALSE_VALUES.items():
            assert dict_get(d, ('b', 'c', key)) is None
            assert dict_get(d, ('b', 'c', key), skip_false_values=False) == false_value