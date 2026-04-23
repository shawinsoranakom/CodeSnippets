def test_use_i18n_false(self):
        """
        makemessages also runs successfully when USE_I18N is False.
        """
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE, encoding="utf-8") as fp:
            po_contents = fp.read()
            # Check two random strings
            self.assertIn("#. Translators: One-line translator comment #1", po_contents)
            self.assertIn('msgctxt "Special trans context #1"', po_contents)