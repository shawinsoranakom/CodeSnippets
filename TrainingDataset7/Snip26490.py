def test_get_empty(self):
        request = self.get_request()
        storage = self.storage_class(request)
        # Overwrite the _get method of the fallback storage to prove it is not
        # used (it would cause a TypeError: 'NoneType' object is not callable).
        self.get_session_storage(storage)._get = None
        self.assertEqual(list(storage), [])