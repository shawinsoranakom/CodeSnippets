def test_buffer_explicit_absolute_filename(self):
        """
        Headers are set correctly with a buffer when an absolute filename is
        provided.
        """
        response = FileResponse(io.BytesIO(b"binary content"), filename=__file__)
        self.assertEqual(response.headers["Content-Length"], "14")
        self.assertEqual(
            response.headers["Content-Disposition"],
            'inline; filename="test_fileresponse.py"',
        )