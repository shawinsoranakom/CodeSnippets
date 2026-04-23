def test_special_char_extracted(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE, encoding="utf-8") as fp:
            po_contents = fp.read()
            self.assertMsgId("Non-breaking space\u00a0:", po_contents)