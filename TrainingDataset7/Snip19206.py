def test_get_backend_timeout_method(self):
        positive_timeout = 10
        positive_backend_timeout = cache.get_backend_timeout(positive_timeout)
        self.assertEqual(positive_backend_timeout, positive_timeout)

        negative_timeout = -5
        negative_backend_timeout = cache.get_backend_timeout(negative_timeout)
        self.assertEqual(negative_backend_timeout, 0)

        none_timeout = None
        none_backend_timeout = cache.get_backend_timeout(none_timeout)
        self.assertIsNone(none_backend_timeout)