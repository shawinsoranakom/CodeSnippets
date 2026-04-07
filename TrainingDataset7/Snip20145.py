def test_lookups_caching(self):
        field = Article._meta.get_field("author")

        # clear and re-cache
        field.get_class_lookups.cache_clear()
        self.assertNotIn("exactly", field.get_lookups())

        # registration should bust the cache
        with register_lookup(models.ForeignObject, Exactly):
            # getting the lookups again should re-cache
            self.assertIn("exactly", field.get_lookups())
        # Unregistration should bust the cache.
        self.assertNotIn("exactly", field.get_lookups())