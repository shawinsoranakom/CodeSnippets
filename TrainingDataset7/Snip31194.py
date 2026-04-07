def test_content_disposition_buffer_explicit_filename(self):
        dispositions = (
            (False, "inline"),
            (True, "attachment"),
        )
        for as_attachment, header_disposition in dispositions:
            response = FileResponse(
                io.BytesIO(b"binary content"),
                as_attachment=as_attachment,
                filename="custom_name.py",
            )
            self.assertEqual(
                response.headers["Content-Disposition"],
                '%s; filename="custom_name.py"' % header_disposition,
            )