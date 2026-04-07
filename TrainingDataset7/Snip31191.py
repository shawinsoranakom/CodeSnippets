def test_content_disposition_escaping(self):
        # fmt: off
        tests = [
            (
                'multi-part-one";\" dummy".txt',
                r"multi-part-one\";\" dummy\".txt"
            ),
        ]
        # fmt: on
        # Non-escape sequence backslashes are path segments on Windows, and are
        # eliminated by an os.path.basename() check in FileResponse.
        if sys.platform != "win32":
            # fmt: off
            tests += [
                (
                    'multi-part-one\\";\" dummy".txt',
                    r"multi-part-one\\\";\" dummy\".txt"
                ),
                (
                    'multi-part-one\\";\\\" dummy".txt',
                    r"multi-part-one\\\";\\\" dummy\".txt"
                )
            ]
            # fmt: on
        for filename, escaped in tests:
            with self.subTest(filename=filename, escaped=escaped):
                response = FileResponse(
                    io.BytesIO(b"binary content"), filename=filename, as_attachment=True
                )
                response.close()
                self.assertEqual(
                    response.headers["Content-Disposition"],
                    f'attachment; filename="{escaped}"',
                )