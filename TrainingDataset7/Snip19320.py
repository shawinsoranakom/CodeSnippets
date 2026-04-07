def test_allowed_async_unsafe_set(self):
        self.assertEqual(check_async_unsafe(None), [E001])