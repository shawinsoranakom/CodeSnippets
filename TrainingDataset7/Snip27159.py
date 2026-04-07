def test_makemigrations_app_name_specified_as_label(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            call_command("makemigrations", "django.contrib.auth", stderr=err)
        self.assertIn(self.did_you_mean_auth_error, err.getvalue())