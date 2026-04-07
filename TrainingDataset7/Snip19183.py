def test_set_many_returns_failing_keys(self):
        def fail_set_multi(mapping, *args, **kwargs):
            return mapping.keys()

        with mock.patch.object(cache._class, "set_multi", side_effect=fail_set_multi):
            failing_keys = cache.set_many({"key": "value"})
            self.assertEqual(failing_keys, ["key"])