def test_with_blank_cache(self, shelve, fn, key):
        assert shelve == {}
        assert fn() == 'test'
        assert shelve == {key: {'etag': '0', 'value': 'test'}}