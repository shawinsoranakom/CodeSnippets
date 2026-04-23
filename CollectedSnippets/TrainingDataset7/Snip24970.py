def test_valid_locale_with_numeric_region_code(self):
        out = StringIO()
        management.call_command(
            "makemessages", locale=["ar_002"], stdout=out, verbosity=1
        )
        self.assertNotIn("invalid locale ar_002", out.getvalue())
        self.assertIn("processing locale ar_002", out.getvalue())
        self.assertIs(Path("locale/ar_002/LC_MESSAGES/django.po").exists(), True)