def test_invalid_locale_private_subtag(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["nl-nl-x-informal"], stdout=out, verbosity=1
        )
        self.assertIn(
            "invalid locale nl-nl-x-informal, did you mean nl_NL-x-informal?",
            out.getvalue(),
        )
        self.assertNotIn("processing locale nl-nl-x-informal", out.getvalue())
        self.assertIs(
            Path("locale/nl-nl-x-informal/LC_MESSAGES/django.po").exists(), False
        )