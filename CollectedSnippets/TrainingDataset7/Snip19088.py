def test_default_used_when_none_is_set(self):
        """If None is cached, get() returns it instead of the default."""
        cache.set("key_default_none", None)
        self.assertIsNone(cache.get("key_default_none", default="default"))