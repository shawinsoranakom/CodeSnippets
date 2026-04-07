def test_upload_interrupted_temporary_file_handler(self):
        # Simulate an interrupted upload by omitting the closing boundary.
        class MockedParser(Parser):
            def __iter__(self):
                for item in super().__iter__():
                    item_type, meta_data, field_stream = item
                    yield item_type, meta_data, field_stream
                    if item_type == FILE:
                        return

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"a")
            temp_file.seek(0)
            with mock.patch(
                "django.http.multipartparser.Parser",
                MockedParser,
            ):
                response = self.client.post(
                    "/temp_file/upload_interrupted/",
                    {"file": temp_file},
                )
            temp_path = response.json()["temp_path"]
            self.assertIs(os.path.exists(temp_path), False)