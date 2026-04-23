def test_symlink(self):
        if symlinks_supported():
            os.symlink(os.path.join(self.test_dir, "templates"), self.symlinked_dir)
        else:
            self.skipTest(
                "os.symlink() not available on this OS + Python version combination."
            )
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, symlinks=True
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            self.assertMsgId("This literal should be included.", po_contents)
        self.assertLocationCommentPresent(
            self.PO_FILE, None, "templates_symlinked", "test.html"
        )