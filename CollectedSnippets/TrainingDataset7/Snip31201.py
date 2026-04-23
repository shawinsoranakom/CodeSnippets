def test_repr(self):
        response = FileResponse(io.BytesIO(b"binary content"))
        self.assertEqual(
            repr(response),
            '<FileResponse status_code=200, "application/octet-stream">',
        )