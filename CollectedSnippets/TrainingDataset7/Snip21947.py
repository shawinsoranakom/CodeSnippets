def test_simple_upload(self):
        with open(__file__, "rb") as fp:
            post_data = {
                "name": "Ringo",
                "file_field": fp,
            }
            response = self.client.post("/upload/", post_data)
        self.assertEqual(response.status_code, 200)