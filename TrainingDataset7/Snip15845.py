def test_precedence(self):
        """
        Apps listed first in INSTALLED_APPS have precedence.
        """
        with self.settings(
            INSTALLED_APPS=[
                "admin_scripts.complex_app",
                "admin_scripts.simple_app",
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ]
        ):
            out = StringIO()
            call_command("duplicate", stdout=out)
            self.assertEqual(out.getvalue().strip(), "complex_app")
        with self.settings(
            INSTALLED_APPS=[
                "admin_scripts.simple_app",
                "admin_scripts.complex_app",
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ]
        ):
            out = StringIO()
            call_command("duplicate", stdout=out)
            self.assertEqual(out.getvalue().strip(), "simple_app")