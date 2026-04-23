def test_valid_locale(self):
        out = StringIO()
        management.call_command("makemessages", locale=["de"], stdout=out, verbosity=1)
        self.assertNotIn("invalid locale de", out.getvalue())
        self.assertIn("processing locale de", out.getvalue())
        self.assertIs(Path(self.PO_FILE).exists(), True)