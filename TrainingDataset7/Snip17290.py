def test_cached_properties_cleared_after_cache_clear(self):
        opts = apps.get_model("admin", "LogEntry")._meta

        cached_properties = [
            name
            for name, attr in models.options.Options.__dict__.items()
            if isinstance(attr, cached_property)
        ]

        # Access each cached property to populate the cache.
        for attr_name in cached_properties:
            getattr(opts, attr_name)
            self.assertIn(attr_name, opts.__dict__)

        apps.clear_cache()

        for attr_name in cached_properties:
            with self.subTest(property=attr_name):
                self.assertNotIn(attr_name, opts.__dict__)