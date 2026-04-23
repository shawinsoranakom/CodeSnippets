def clear_cache(self):
        """
        Clear all internal caches, for methods that alter the app registry.

        This is mostly used in tests.
        """
        self.get_swappable_settings_name.cache_clear()
        # Call expire cache on each model. This will purge
        # the relation tree and the fields cache.
        self.get_models.cache_clear()
        if self.ready:
            # Circumvent self.get_models() to prevent that the cache is
            # refilled. This particularly prevents that an empty value is
            # cached while cloning.
            for app_config in self.app_configs.values():
                for model in app_config.get_models(include_auto_created=True):
                    model._meta._expire_cache()