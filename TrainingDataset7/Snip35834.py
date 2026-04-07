def test_urlconf(self):
        response = self.client.get("/test/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content, b"outer:/test/me/,inner:/inner_urlconf/second_test/"
        )
        response = self.client.get("/inner_urlconf/second_test/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/second_test/")
        self.assertEqual(response.status_code, 404)