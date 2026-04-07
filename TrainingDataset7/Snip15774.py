def test_complex_app(self):
        """manage.py check does not raise an ImportError validating a
        complex app with nested calls to load_app"""

        self.write_settings(
            "settings.py",
            apps=[
                "admin_scripts.complex_app",
                "admin_scripts.simple_app",
                "django.contrib.admin.apps.SimpleAdminConfig",
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.messages",
            ],
            sdict={
                "DEBUG": True,
                "MIDDLEWARE": [
                    "django.contrib.messages.middleware.MessageMiddleware",
                    "django.contrib.auth.middleware.AuthenticationMiddleware",
                    "django.contrib.sessions.middleware.SessionMiddleware",
                ],
                "TEMPLATES": [
                    {
                        "BACKEND": "django.template.backends.django.DjangoTemplates",
                        "DIRS": [],
                        "APP_DIRS": True,
                        "OPTIONS": {
                            "context_processors": [
                                "django.template.context_processors.request",
                                "django.contrib.auth.context_processors.auth",
                                "django.contrib.messages.context_processors.messages",
                            ],
                        },
                    },
                ],
            },
        )
        args = ["check"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertEqual(out, "System check identified no issues (0 silenced).\n")