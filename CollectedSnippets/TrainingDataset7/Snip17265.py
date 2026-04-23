def test_get_models_only_returns_installed_models(self):
        self.assertNotIn("NotInstalledModel", [m.__name__ for m in apps.get_models()])