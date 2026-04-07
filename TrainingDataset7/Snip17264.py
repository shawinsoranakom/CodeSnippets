def test_get_model_only_returns_installed_models(self):
        with self.assertRaises(LookupError):
            apps.get_model("not_installed", "NotInstalledModel")