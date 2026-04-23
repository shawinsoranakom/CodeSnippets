def test_default_never_expiring_timeout(self):
        # Regression test for #22845
        with self.settings(
            CACHES=caches_setting_for_tests(
                base=self.base_params, exclude=memcached_excluded_caches, TIMEOUT=None
            )
        ):
            cache.set("infinite_foo", "bar")
            self.assertEqual(cache.get("infinite_foo"), "bar")