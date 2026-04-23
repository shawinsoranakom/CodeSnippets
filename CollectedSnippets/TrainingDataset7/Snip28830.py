def tearDown(self):
        for model in Article, Authors, Reviewers, Scientist:
            model._meta.managed = False

        apps.app_configs["model_options"].models = self._old_models
        apps.all_models["model_options"] = self._old_models
        apps.clear_cache()