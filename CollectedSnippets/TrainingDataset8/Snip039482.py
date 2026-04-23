def test_cache_stats_provider():
    caches = caching._mem_caches
    caches.clear()

    init_size = sum(stat.byte_length for stat in caches.get_stats())
    assert init_size == 0
    assert len(caches.get_stats()) == 0

    @st.cache
    def foo():
        return 42

    foo()
    new_size = sum(stat.byte_length for stat in caches.get_stats())
    assert new_size > 0
    assert len(caches.get_stats()) == 1

    foo()
    new_size_2 = sum(stat.byte_length for stat in caches.get_stats())
    assert new_size_2 == new_size

    @st.cache
    def bar(i):
        return 0

    bar(0)
    new_size_3 = sum(stat.byte_length for stat in caches.get_stats())
    assert new_size_3 > new_size_2
    assert len(caches.get_stats()) == 2

    bar(1)
    new_size_4 = sum(stat.byte_length for stat in caches.get_stats())
    assert new_size_4 > new_size_3
    assert len(caches.get_stats()) == 3