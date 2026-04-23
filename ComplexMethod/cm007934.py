def test_lru_eviction(self, ie, logger):
        MAX_SIZE = 2
        provider = MemoryLRUPCP(ie, logger, {}, initialize_cache=lambda max_size: (OrderedDict(), threading.Lock(), MAX_SIZE))
        provider.store('key1', 'value1', int(time.time()) + 5)
        provider.store('key2', 'value2', int(time.time()) + 5)
        assert len(provider.cache) == 2

        assert provider.get('key1') == 'value1'

        provider.store('key3', 'value3', int(time.time()) + 5)
        assert len(provider.cache) == 2

        assert provider.get('key2') is None

        provider.store('key4', 'value4', int(time.time()) + 5)
        assert len(provider.cache) == 2

        assert provider.get('key1') is None
        assert provider.get('key3') == 'value3'
        assert provider.get('key4') == 'value4'