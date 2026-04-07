def test_serializer_dumps(self):
        self.assertEqual(cache._cache._serializer.dumps(123), 123)
        self.assertIsInstance(cache._cache._serializer.dumps(True), bytes)
        self.assertIsInstance(cache._cache._serializer.dumps("abc"), bytes)