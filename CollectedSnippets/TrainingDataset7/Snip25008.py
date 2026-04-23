def test_copy_plural_forms(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            self.assertIn("Plural-Forms: nplurals=2; plural=(n != 1)", po_contents)