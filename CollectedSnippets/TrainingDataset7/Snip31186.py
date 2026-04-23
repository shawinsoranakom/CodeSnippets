def test_content_type_buffer(self):
        response = FileResponse(io.BytesIO(b"binary content"))
        self.assertEqual(response.headers["Content-Type"], "application/octet-stream")