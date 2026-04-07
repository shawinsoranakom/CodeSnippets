def test_content_disposition_buffer(self):
        response = FileResponse(io.BytesIO(b"binary content"))
        self.assertFalse(response.has_header("Content-Disposition"))