def test_cache_without_limit(self):
        maximum = 10**4
        cache = LocalWeakReferencedCache()
        refs = []
        for x in range(maximum):
            refs.append(Request(f"https://example.org/{x}"))
            cache[refs[-1]] = x
        assert len(cache) == maximum
        for i, r in enumerate(refs):
            assert r in cache
            assert cache[r] == i
        del r  # delete reference to the last object in the list  # pylint: disable=undefined-loop-variable

        # delete half of the objects, make sure that is reflected in the cache
        for _ in range(maximum // 2):
            refs.pop()

        # PyPy takes longer to collect dead references
        garbage_collect()

        assert len(cache) == maximum // 2
        for i, r in enumerate(refs):
            assert r in cache
            assert cache[r] == i