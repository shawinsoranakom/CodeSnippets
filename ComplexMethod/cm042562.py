def test_cache_with_limit(self):
        cache = LocalWeakReferencedCache(limit=2)
        r1 = Request("https://example.org")
        r2 = Request("https://example.com")
        r3 = Request("https://example.net")
        cache[r1] = 1
        cache[r2] = 2
        cache[r3] = 3
        assert len(cache) == 2
        assert r1 not in cache
        assert r2 in cache
        assert r3 in cache
        assert cache[r1] is None
        assert cache[r2] == 2
        assert cache[r3] == 3
        del r2

        # PyPy takes longer to collect dead references
        garbage_collect()

        assert len(cache) == 1