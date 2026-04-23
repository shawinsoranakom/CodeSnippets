def test_basic(self):
        tests = (
            ((False, None), None),
            ((False, "example"), 'inline; filename="example"'),
            ((True, None), "attachment"),
            ((True, "example"), 'attachment; filename="example"'),
            (
                (True, '"example" file\\name'),
                'attachment; filename="\\"example\\" file\\\\name"',
            ),
            ((True, "espécimen"), "attachment; filename*=utf-8''esp%C3%A9cimen"),
            (
                (True, '"espécimen" filename'),
                "attachment; filename*=utf-8''%22esp%C3%A9cimen%22%20filename",
            ),
            ((True, "some\nfile"), "attachment; filename*=utf-8''some%0Afile"),
        )

        for (is_attachment, filename), expected in tests:
            with self.subTest(is_attachment=is_attachment, filename=filename):
                self.assertEqual(
                    content_disposition_header(is_attachment, filename), expected
                )