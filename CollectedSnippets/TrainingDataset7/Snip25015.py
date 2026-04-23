def test_location_comments_for_templatized_files(self):
        """
        Ensure no leaky paths in comments, e.g. #: path\to\file.html.py:123
        Refs #21209/#26341.
        """
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
        self.assertMsgId("#: templates/test.html.py", po_contents)
        self.assertLocationCommentNotPresent(self.PO_FILE, None, ".html.py")
        self.assertLocationCommentPresent(self.PO_FILE, 5, "templates", "test.html")