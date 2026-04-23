def test_content_disposition_file(self):
        filenames = (
            ("", "test_fileresponse.py"),
            ("custom_name.py", "custom_name.py"),
        )
        dispositions = (
            (False, "inline"),
            (True, "attachment"),
        )
        for (filename, header_filename), (
            as_attachment,
            header_disposition,
        ) in itertools.product(filenames, dispositions):
            with self.subTest(filename=filename, disposition=header_disposition):
                response = FileResponse(
                    open(__file__, "rb"), filename=filename, as_attachment=as_attachment
                )
                response.close()
                self.assertEqual(
                    response.headers["Content-Disposition"],
                    '%s; filename="%s"' % (header_disposition, header_filename),
                )