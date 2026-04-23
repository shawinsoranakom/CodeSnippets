def test_uploading_temp_file(self):
        with tempfile.TemporaryFile() as test_file:
            response = self.client.post("/upload_view/", data={"temp_file": test_file})
        self.assertEqual(response.content, b"temp_file")