def test_uploading_named_temp_file(self):
        with tempfile.NamedTemporaryFile() as test_file:
            response = self.client.post(
                "/upload_view/",
                data={"named_temp_file": test_file},
            )
        self.assertEqual(response.content, b"named_temp_file")