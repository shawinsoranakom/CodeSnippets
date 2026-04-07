def test_invalid_locale_start_with_underscore(self):
        out = StringIO()
        management.call_command("makemessages", locale=["_en"], stdout=out, verbosity=1)
        self.assertIn("invalid locale _en", out.getvalue())
        self.assertNotIn("processing locale _en", out.getvalue())
        self.assertIs(Path("locale/_en/LC_MESSAGES/django.po").exists(), False)