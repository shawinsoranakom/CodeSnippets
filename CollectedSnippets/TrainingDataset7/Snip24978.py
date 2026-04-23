def test_invalid_locale_end_with_underscore(self):
        out = StringIO()
        management.call_command("makemessages", locale=["en_"], stdout=out, verbosity=1)
        self.assertIn("invalid locale en_", out.getvalue())
        self.assertNotIn("processing locale en_", out.getvalue())
        self.assertIs(Path("locale/en_/LC_MESSAGES/django.po").exists(), False)