def test_models_not_loaded(self):
        """
        apps.get_models() raises an exception if apps.models_ready isn't True.
        """
        apps.models_ready = False
        try:
            # The cache must be cleared to trigger the exception.
            apps.get_models.cache_clear()
            with self.assertRaisesMessage(
                AppRegistryNotReady, "Models aren't loaded yet."
            ):
                apps.get_models()
        finally:
            apps.models_ready = True