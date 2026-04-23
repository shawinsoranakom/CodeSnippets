def test_cache_versioning_get_set_many(self):
        # set, using default version = 1
        cache.set_many({"ford1": 37, "arthur1": 42})
        self.assertEqual(
            cache.get_many(["ford1", "arthur1"]), {"ford1": 37, "arthur1": 42}
        )
        self.assertEqual(
            cache.get_many(["ford1", "arthur1"], version=1),
            {"ford1": 37, "arthur1": 42},
        )
        self.assertEqual(cache.get_many(["ford1", "arthur1"], version=2), {})

        self.assertEqual(caches["v2"].get_many(["ford1", "arthur1"]), {})
        self.assertEqual(
            caches["v2"].get_many(["ford1", "arthur1"], version=1),
            {"ford1": 37, "arthur1": 42},
        )
        self.assertEqual(caches["v2"].get_many(["ford1", "arthur1"], version=2), {})

        # set, default version = 1, but manually override version = 2
        cache.set_many({"ford2": 37, "arthur2": 42}, version=2)
        self.assertEqual(cache.get_many(["ford2", "arthur2"]), {})
        self.assertEqual(cache.get_many(["ford2", "arthur2"], version=1), {})
        self.assertEqual(
            cache.get_many(["ford2", "arthur2"], version=2),
            {"ford2": 37, "arthur2": 42},
        )

        self.assertEqual(
            caches["v2"].get_many(["ford2", "arthur2"]), {"ford2": 37, "arthur2": 42}
        )
        self.assertEqual(caches["v2"].get_many(["ford2", "arthur2"], version=1), {})
        self.assertEqual(
            caches["v2"].get_many(["ford2", "arthur2"], version=2),
            {"ford2": 37, "arthur2": 42},
        )

        # v2 set, using default version = 2
        caches["v2"].set_many({"ford3": 37, "arthur3": 42})
        self.assertEqual(cache.get_many(["ford3", "arthur3"]), {})
        self.assertEqual(cache.get_many(["ford3", "arthur3"], version=1), {})
        self.assertEqual(
            cache.get_many(["ford3", "arthur3"], version=2),
            {"ford3": 37, "arthur3": 42},
        )

        self.assertEqual(
            caches["v2"].get_many(["ford3", "arthur3"]), {"ford3": 37, "arthur3": 42}
        )
        self.assertEqual(caches["v2"].get_many(["ford3", "arthur3"], version=1), {})
        self.assertEqual(
            caches["v2"].get_many(["ford3", "arthur3"], version=2),
            {"ford3": 37, "arthur3": 42},
        )

        # v2 set, default version = 2, but manually override version = 1
        caches["v2"].set_many({"ford4": 37, "arthur4": 42}, version=1)
        self.assertEqual(
            cache.get_many(["ford4", "arthur4"]), {"ford4": 37, "arthur4": 42}
        )
        self.assertEqual(
            cache.get_many(["ford4", "arthur4"], version=1),
            {"ford4": 37, "arthur4": 42},
        )
        self.assertEqual(cache.get_many(["ford4", "arthur4"], version=2), {})

        self.assertEqual(caches["v2"].get_many(["ford4", "arthur4"]), {})
        self.assertEqual(
            caches["v2"].get_many(["ford4", "arthur4"], version=1),
            {"ford4": 37, "arthur4": 42},
        )
        self.assertEqual(caches["v2"].get_many(["ford4", "arthur4"], version=2), {})