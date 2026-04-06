def test_with_filled_cache(self, shelve, fn, key):
        cache_value = {key: {'etag': '0', 'value': 'new-value'}}
        shelve.update(cache_value)
        assert fn() == 'new-value'
        assert shelve == cache_value