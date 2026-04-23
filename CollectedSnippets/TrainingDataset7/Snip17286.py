def test_get_app_config(self):
        """
        Tests apps.get_app_config().
        """
        app_config = apps.get_app_config("admin")
        self.assertEqual(app_config.name, "django.contrib.admin")

        app_config = apps.get_app_config("staticfiles")
        self.assertEqual(app_config.name, "django.contrib.staticfiles")

        with self.assertRaises(LookupError):
            apps.get_app_config("admindocs")

        msg = "No installed app with label 'django.contrib.auth'. Did you mean 'myauth'"
        with self.assertRaisesMessage(LookupError, msg):
            apps.get_app_config("django.contrib.auth")