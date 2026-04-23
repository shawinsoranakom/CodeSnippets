def setUp(self):
        super().setUp()
        self._old_models = apps.app_configs["migrations"].models.copy()