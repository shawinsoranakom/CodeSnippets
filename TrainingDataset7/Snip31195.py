def test_response_buffer(self):
        response = FileResponse(io.BytesIO(b"binary content"))
        self.assertEqual(list(response), [b"binary content"])