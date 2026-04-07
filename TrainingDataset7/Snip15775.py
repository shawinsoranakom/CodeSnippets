def test_app_with_import(self):
        """manage.py check does not raise errors when an app imports a base
        class that itself has an abstract base."""

        self.write_settings(
            "settings.py",
            apps=[
                "admin_scripts.app_with_import",
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sites",
            ],
            sdict={"DEBUG": True},
        )
        args = ["check"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertEqual(out, "System check identified no issues (0 silenced).\n")