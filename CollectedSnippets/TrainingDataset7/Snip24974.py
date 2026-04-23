def test_invalid_locale_hyphen(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["pl-PL"], stdout=out, verbosity=1
        )
        self.assertIn("invalid locale pl-PL, did you mean pl_PL?", out.getvalue())
        self.assertNotIn("processing locale pl-PL", out.getvalue())
        self.assertIs(Path("locale/pl-PL/LC_MESSAGES/django.po").exists(), False)