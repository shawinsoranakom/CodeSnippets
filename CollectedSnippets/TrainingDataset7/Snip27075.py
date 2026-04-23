def tearDown(self):
        apps.app_configs["migrations"].models = self._old_models
        apps.all_models["migrations"] = self._old_models
        apps.clear_cache()
        super().tearDown()