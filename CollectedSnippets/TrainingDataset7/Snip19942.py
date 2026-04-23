def setUp(self):
        app_config = apps.get_app_config("contenttypes_tests")
        models.signals.post_migrate.connect(
            self.assertOperationsInjected, sender=app_config
        )
        self.addCleanup(
            models.signals.post_migrate.disconnect,
            self.assertOperationsInjected,
            sender=app_config,
        )