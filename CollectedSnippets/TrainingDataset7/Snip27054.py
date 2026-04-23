def test_sqlmigrate_transaction_keywords_not_colorized(self):
        out = io.StringIO()
        with mock.patch(
            "django.core.management.color.supports_color", lambda *args: True
        ):
            call_command("sqlmigrate", "migrations", "0001", stdout=out, no_color=False)
        self.assertNotIn("\x1b", out.getvalue())