def test_check_for_language(self):
        with tempfile.TemporaryDirectory() as app_dir:
            os.makedirs(os.path.join(app_dir, "locale", "dummy_Lang", "LC_MESSAGES"))
            open(
                os.path.join(
                    app_dir, "locale", "dummy_Lang", "LC_MESSAGES", "django.mo"
                ),
                "w",
            ).close()
            app_config = AppConfig("dummy_app", AppModuleStub(__path__=[app_dir]))
            with mock.patch(
                "django.apps.apps.get_app_configs", return_value=[app_config]
            ):
                self.assertIs(check_for_language("dummy-lang"), True)