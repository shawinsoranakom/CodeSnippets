def test_healthz_with_csrf(self):
        response = self.fetch("/healthz")
        self.assertEqual(200, response.code)
        self.assertEqual(b"ok", response.body)
        self.assertIn("Set-Cookie", response.headers)