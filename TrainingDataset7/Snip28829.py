def setUp(self):
        # The unmanaged models need to be removed after the test in order to
        # prevent bad interactions with the flush operation in other tests.
        self._old_models = apps.app_configs["model_options"].models.copy()

        for model in Article, Authors, Reviewers, Scientist:
            model._meta.managed = True