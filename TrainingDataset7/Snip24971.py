def test_valid_locale_tachelhit_latin_morocco(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["shi_Latn_MA"], stdout=out, verbosity=1
        )
        self.assertNotIn("invalid locale shi_Latn_MA", out.getvalue())
        self.assertIn("processing locale shi_Latn_MA", out.getvalue())
        self.assertIs(Path("locale/shi_Latn_MA/LC_MESSAGES/django.po").exists(), True)