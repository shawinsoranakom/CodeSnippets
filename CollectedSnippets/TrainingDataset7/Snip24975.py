def test_invalid_locale_lower_country(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["pl_pl"], stdout=out, verbosity=1
        )
        self.assertIn("invalid locale pl_pl, did you mean pl_PL?", out.getvalue())
        self.assertNotIn("processing locale pl_pl", out.getvalue())
        self.assertIs(Path("locale/pl_pl/LC_MESSAGES/django.po").exists(), False)