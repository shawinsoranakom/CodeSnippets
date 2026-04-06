def test_when_etag_changed(self, shelve, fn, key):
        shelve.update({key: {'etag': '-1', 'value': 'old-value'}})
        assert fn() == 'test'
        assert shelve == {key: {'etag': '0', 'value': 'test'}}