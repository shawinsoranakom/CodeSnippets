def test_content_length_buffer(self):
        response = FileResponse(io.BytesIO(b"binary content"))
        self.assertEqual(response.headers["Content-Length"], "14")