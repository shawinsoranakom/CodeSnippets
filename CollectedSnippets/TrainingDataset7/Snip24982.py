def test_blocktranslate_trimmed(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            # should not be trimmed
            self.assertNotMsgId("Text with a few line breaks.", po_contents)
            # should be trimmed
            self.assertMsgId(
                "Again some text with a few line breaks, this time should be trimmed.",
                po_contents,
            )
        # #21406 -- Should adjust for eaten line numbers
        self.assertMsgId("Get my line number", po_contents)
        self.assertLocationCommentPresent(
            self.PO_FILE, "Get my line number", "templates", "test.html"
        )