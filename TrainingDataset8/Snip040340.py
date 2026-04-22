def test_endpoint(self):
        response = self.fetch("/script-health-check")
        self.assertEqual(404, response.code)