def test_file_passes(self):
        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="file1"; '
                    'filename="test.file"',
                    "",
                    "value",
                    "--boundary--",
                ]
            )
        )
        request = WSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=boundary",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        with self.settings(DATA_UPLOAD_MAX_MEMORY_SIZE=1):
            request._load_post_and_files()
            self.assertIn("file1", request.FILES, "Upload file not present")