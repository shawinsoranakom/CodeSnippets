def test_no_wrap_enabled(self):
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, no_wrap=True
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            self.assertMsgId(
                "This literal should also be included wrapped or not wrapped "
                "depending on the use of the --no-wrap option.",
                po_contents,
            )