def test_no_settings(self):
        test_environ = os.environ.copy()
        if "DJANGO_SETTINGS_MODULE" in test_environ:
            del test_environ["DJANGO_SETTINGS_MODULE"]
        error = (
            "Automatic imports are disabled since settings are not configured.\n"
            "DJANGO_SETTINGS_MODULE value is None.\n"
            "HINT: Ensure that the settings module is configured and set.\n\n"
        )
        for verbosity, assertError in [
            ("0", self.assertNotIn),
            ("1", self.assertIn),
            ("2", self.assertIn),
        ]:
            with self.subTest(verbosity=verbosity, get_auto_imports="models"):
                p = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "django",
                        "shell",
                        "-c",
                        "print(globals())",
                        "-v",
                        verbosity,
                    ],
                    capture_output=True,
                    env=test_environ,
                    text=True,
                    umask=-1,
                )
                assertError(error, p.stdout)
                self.assertNotIn("Marker", p.stdout)
                self.assertNotIn("reset_queries", p.stdout)
                self.assertNotIn("imported automatically", p.stdout)

            with self.subTest(verbosity=verbosity, get_auto_imports="without-models"):
                with mock.patch(
                    "django.core.management.commands.shell.Command.get_auto_imports",
                    return_value=["django.urls.resolve"],
                ):
                    p = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "django",
                            "shell",
                            "-c",
                            "print(globals())",
                            "-v",
                            verbosity,
                        ],
                        capture_output=True,
                        env=test_environ,
                        text=True,
                        umask=-1,
                    )
                    assertError(error, p.stdout)
                    self.assertNotIn("resolve", p.stdout)