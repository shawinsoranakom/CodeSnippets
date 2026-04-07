def test_egg1(self):
        """Models module can be loaded from an app in an egg"""
        egg_name = "%s/modelapp.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            with self.settings(INSTALLED_APPS=["app_with_models"]):
                models_module = apps.get_app_config("app_with_models").models_module
                self.assertIsNotNone(models_module)
        del apps.all_models["app_with_models"]