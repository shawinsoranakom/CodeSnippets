def test_valid_locale_private_subtag(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["nl_NL-x-informal"], stdout=out, verbosity=1
        )
        self.assertNotIn("invalid locale nl_NL-x-informal", out.getvalue())
        self.assertIn("processing locale nl_NL-x-informal", out.getvalue())
        self.assertIs(
            Path("locale/nl_NL-x-informal/LC_MESSAGES/django.po").exists(), True
        )