def test_optimizemigration_app_name_specified_as_label(self):
        with self.assertRaisesMessage(CommandError, self.did_you_mean_auth_error):
            call_command("optimizemigration", "django.contrib.auth", "0002")