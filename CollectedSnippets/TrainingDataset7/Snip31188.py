def test_content_type_buffer_explicit_default(self):
        response = FileResponse(
            io.BytesIO(b"binary content"), content_type="text/html; charset=utf-8"
        )
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")