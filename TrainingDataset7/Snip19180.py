def test_default_far_future_timeout(self):
        # Regression test for #22845
        with self.settings(
            CACHES=caches_setting_for_tests(
                base=self.base_params,
                exclude=memcached_excluded_caches,
                # 60*60*24*365, 1 year
                TIMEOUT=31536000,
            )
        ):
            cache.set("future_foo", "bar")
            self.assertEqual(cache.get("future_foo"), "bar")