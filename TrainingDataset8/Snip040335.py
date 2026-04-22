def test_endpoint(self):
        response = self.fetch("/script-health-check")
        self.assertEqual(200, response.code)
        self.assertEqual(b"test_message", response.body)