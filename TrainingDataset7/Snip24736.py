def test_streaming(self):
        response = self.client.get("/streaming/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(list(response)), b"streaming content")