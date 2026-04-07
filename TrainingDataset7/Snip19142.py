def test_get_or_set_racing(self):
        with mock.patch(
            "%s.%s" % (settings.CACHES["default"]["BACKEND"], "add")
        ) as cache_add:
            # Simulate cache.add() failing to add a value. In that case, the
            # default value should be returned.
            cache_add.return_value = False
            self.assertEqual(cache.get_or_set("key", "default"), "default")