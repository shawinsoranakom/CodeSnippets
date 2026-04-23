def test_migrate_app_name_specified_as_label(self):
        with self.assertRaisesMessage(CommandError, self.did_you_mean_auth_error):
            call_command("migrate", "django.contrib.auth")