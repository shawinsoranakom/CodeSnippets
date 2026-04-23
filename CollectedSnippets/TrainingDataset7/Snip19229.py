def test_cache_key_varies_by_url(self):
        """
        get_cache_key keys differ by fully-qualified URL instead of path
        """
        request1 = self.factory.get(self.path, headers={"host": "sub-1.example.com"})
        learn_cache_key(request1, HttpResponse())
        request2 = self.factory.get(self.path, headers={"host": "sub-2.example.com"})
        learn_cache_key(request2, HttpResponse())
        self.assertNotEqual(get_cache_key(request1), get_cache_key(request2))