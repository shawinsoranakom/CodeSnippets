def test_available_not_called(self, ie, pot_request, logger):
        # Test that the available method is not called when provider higher in the list is available
        provider_unavailable = create_memory_pcp(
            ie, logger, provider_key='unavailable', provider_name='unavailable', available=False)
        provider_available = create_memory_pcp(ie, logger, provider_key='available', provider_name='available')

        logger.log_level = logger.LogLevel.INFO

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
        assert provider_unavailable.available_called_times == 0
        assert provider_available.available_called_times
        assert 'PO Token Cache Providers: available-0.0.0 (external), unavailable-0.0.0 (external, unavailable)' not in logger.messages.get('trace', [])