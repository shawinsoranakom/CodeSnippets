def test_cache_provider_unavailable_fallback(self, pot_request, ie, logger):
        provider_unavailable = create_memory_pcp(ie, logger, provider_key='unavailable', provider_name='unavailable', available=False)
        provider_available = create_memory_pcp(ie, logger, provider_key='available', provider_name='available')

        cache = PoTokenCache(
            cache_providers=[provider_unavailable, provider_available],
            cache_spec_providers=[ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})],
            logger=logger,
        )

        response = PoTokenResponse(EXAMPLE_PO_TOKEN)
        cache.store(pot_request, response)
        assert cache.get(pot_request) is not None
        assert provider_unavailable.get_calls == 0
        assert provider_unavailable.store_calls == 0
        assert provider_available.get_calls == 1
        assert provider_available.store_calls == 1
        assert provider_unavailable.available_called_times
        assert provider_available.available_called_times

        # should not even try to use the provider for the request
        assert 'Attempting to fetch a PO Token response from "unavailable" provider' not in logger.messages['trace']
        assert 'Attempting to fetch a PO Token response from "available" provider' not in logger.messages['trace']