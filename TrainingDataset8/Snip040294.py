def test_healthz_without_csrf(self):
        response = self.fetch("/healthz")
        self.assertEqual(200, response.code)
        self.assertEqual(b"ok", response.body)
        self.assertNotIn("Set-Cookie", response.headers)