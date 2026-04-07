def test_ignore_file_patterns(self):
        out, po_contents = self._run_makemessages(
            ignore_patterns=[
                "xxx_*",
            ]
        )
        self.assertIn("ignoring file xxx_ignored.html", out)
        self.assertNotMsgId("This should be ignored too.", po_contents)