def test_urlconf_overridden(self):
        response = self.client.get("/test/me/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/inner_urlconf/second_test/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/second_test/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"outer:,inner:/second_test/")