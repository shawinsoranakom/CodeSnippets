def _assert_simple(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"This is a simple view")