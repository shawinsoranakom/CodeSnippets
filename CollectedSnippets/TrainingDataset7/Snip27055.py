def test_sqlmigrate_system_checks_colorized(self):
        with (
            mock.patch(
                "django.core.management.color.supports_color", lambda *args: True
            ),
            self.assertRaisesMessage(SystemCheckError, "\x1b"),
        ):
            call_command(
                "sqlmigrate", "migrations", "0001", skip_checks=False, no_color=False
            )