def test_multiple_locales(self):
        management.call_command("makemessages", locale=["pt", "de"], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE_PT))
        self.assertTrue(os.path.exists(self.PO_FILE_DE))