def test_ignore_subdirectory(self):
        out, po_contents = self._run_makemessages(
            ignore_patterns=[
                "templates/*/ignore.html",
                "templates/subdir/*",
            ]
        )
        self.assertIn("ignoring directory subdir", out)
        self.assertNotMsgId("This subdir should be ignored too.", po_contents)