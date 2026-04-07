def test_percent_symbol_in_po_file(self):
        call_command("compilemessages", locale=[self.LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.MO_FILE))