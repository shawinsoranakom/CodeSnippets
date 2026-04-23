def test_valid_locale_with_country(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["en_GB"], stdout=out, verbosity=1
        )
        self.assertNotIn("invalid locale en_GB", out.getvalue())
        self.assertIn("processing locale en_GB", out.getvalue())
        self.assertIs(Path("locale/en_GB/LC_MESSAGES/django.po").exists(), True)