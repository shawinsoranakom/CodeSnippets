def test_invalid_locale_plus(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["en+GB"], stdout=out, verbosity=1
        )
        self.assertIn("invalid locale en+GB, did you mean en_GB?", out.getvalue())
        self.assertNotIn("processing locale en+GB", out.getvalue())
        self.assertIs(Path("locale/en+GB/LC_MESSAGES/django.po").exists(), False)