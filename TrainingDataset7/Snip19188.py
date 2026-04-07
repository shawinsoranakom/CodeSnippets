def test_pymemcache_highest_pickle_version(self):
        self.assertEqual(
            cache._cache.default_kwargs["serde"]._serialize_func.keywords[
                "pickle_version"
            ],
            pickle.HIGHEST_PROTOCOL,
        )
        for cache_key in settings.CACHES:
            for client_key, client in caches[cache_key]._cache.clients.items():
                with self.subTest(cache_key=cache_key, server=client_key):
                    self.assertEqual(
                        client.serde._serialize_func.keywords["pickle_version"],
                        pickle.HIGHEST_PROTOCOL,
                    )