def test_ignore_directory(self):
        out, po_contents = self._run_makemessages(
            ignore_patterns=[
                os.path.join("ignore_dir", "*"),
            ]
        )
        self.assertIn("ignoring directory ignore_dir", out)
        self.assertMsgId("This literal should be included.", po_contents)
        self.assertNotMsgId("This should be ignored.", po_contents)