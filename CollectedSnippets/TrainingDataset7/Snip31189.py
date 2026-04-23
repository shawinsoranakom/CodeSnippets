def test_content_type_buffer_named(self):
        test_tuples = (
            (__file__, ["text/x-python", "text/plain"]),
            (__file__ + "nosuchfile", ["application/octet-stream"]),
            ("test_fileresponse.py", ["text/x-python", "text/plain"]),
            ("test_fileresponse.pynosuchfile", ["application/octet-stream"]),
        )
        for filename, content_types in test_tuples:
            with self.subTest(filename=filename):
                buffer = io.BytesIO(b"binary content")
                buffer.name = filename
                response = FileResponse(buffer)
                self.assertIn(response.headers["Content-Type"], content_types)