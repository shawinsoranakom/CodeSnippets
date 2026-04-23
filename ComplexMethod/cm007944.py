def test_available_called_trace(self, ie, pot_request, logger):
        # But if logging level is trace should call available (as part of debug logging)
        provider_unavailable = create_memory_pcp(
            ie, logger, provider_key='unavailable', provider_name='unavailable', available=False)
        provider_available = create_memory_pcp(ie, logger, provider_key='available', provider_name='available')

        logger.log_level = logger.LogLevel.TRACE

        cache = PoTokenCache(
            cache_providers=[provider_available, provider_unavailable],
            cache_spec_providers=[ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})],
            logger=logger,
        )

        response = PoTokenResponse(EXAMPLE_PO_TOKEN)
        cache.store(pot_request, response, write_policy=CacheProviderWritePolicy.WRITE_FIRST)
        assert cache.get(pot_request) is not None
        assert provider_unavailable.get_calls == 0
        assert provider_unavailable.store_calls == 0
        assert provider_available.get_calls == 1
        assert provider_available.store_calls == 1
        assert provider_unavailable.available_called_times
        assert provider_available.available_called_times
        assert 'PO Token Cache Providers: available-0.0.0 (external), unavailable-0.0.0 (external, unavailable)' in logger.messages.get('trace', [])