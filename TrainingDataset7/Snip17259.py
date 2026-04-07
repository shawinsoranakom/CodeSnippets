def test_egg2(self):
        """
        Loading an app from an egg that has no models returns no models (and no
        error).
        """
        egg_name = "%s/nomodelapp.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            with self.settings(INSTALLED_APPS=["app_no_models"]):
                models_module = apps.get_app_config("app_no_models").models_module
                self.assertIsNone(models_module)
        del apps.all_models["app_no_models"]