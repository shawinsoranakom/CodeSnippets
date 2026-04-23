def test_invalid_locale_uppercase(self):
        out = StringIO()
        management.call_command("makemessages", locale=["PL"], stdout=out, verbosity=1)
        self.assertIn("invalid locale PL, did you mean pl?", out.getvalue())
        self.assertNotIn("processing locale pl", out.getvalue())
        self.assertIs(Path("locale/pl/LC_MESSAGES/django.po").exists(), False)