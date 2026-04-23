def test_nonexistent_alias(self):
        msg = "The connection 'nonexistent' doesn't exist."
        with self.assertRaisesMessage(InvalidCacheBackendError, msg):
            caches["nonexistent"]