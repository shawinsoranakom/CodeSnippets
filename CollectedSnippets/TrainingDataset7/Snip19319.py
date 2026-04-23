def test_no_allowed_async_unsafe(self):
        self.assertEqual(check_async_unsafe(None), [])