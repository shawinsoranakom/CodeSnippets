def test_no_obsolete(self):
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, no_obsolete=True
        )
        self.assertIs(os.path.exists(self.PO_FILE), True)
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            self.assertNotIn('#~ msgid "Obsolete string."', po_contents)
            self.assertNotIn('#~ msgstr "Translated obsolete string."', po_contents)
            self.assertMsgId("This is a translatable string.", po_contents)
            self.assertMsgStr("This is a translated string.", po_contents)