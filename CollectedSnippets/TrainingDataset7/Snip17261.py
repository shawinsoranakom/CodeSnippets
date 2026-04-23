def test_egg4(self):
        """
        Loading an app with no models from under the top-level egg package
        generates no error.
        """
        egg_name = "%s/omelet.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            with self.settings(INSTALLED_APPS=["omelet.app_no_models"]):
                models_module = apps.get_app_config("app_no_models").models_module
                self.assertIsNone(models_module)
        del apps.all_models["app_no_models"]