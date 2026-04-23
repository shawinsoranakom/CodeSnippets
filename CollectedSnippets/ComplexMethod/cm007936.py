def test_unsupported_cache_spec_fallback(self, memorypcp, pot_request, ie, logger):
        unsupported_provider = UnsupportedCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        example_provider = ExampleCacheSpecProviderPCSP(ie=ie, logger=logger, settings={})
        cache = PoTokenCache(
            cache_providers=[memorypcp],
            cache_spec_providers=[unsupported_provider, example_provider],
            logger=logger,
        )

        response = PoTokenResponse(EXAMPLE_PO_TOKEN)

        assert cache.get(pot_request) is None
        assert unsupported_provider.generate_called_times == 1
        assert example_provider.generate_called_times == 1

        cache.store(pot_request, response)
        assert unsupported_provider.generate_called_times == 2
        assert example_provider.generate_called_times == 2

        cached_response = cache.get(pot_request)
        assert unsupported_provider.generate_called_times == 3
        assert example_provider.generate_called_times == 3
        assert cached_response is not None
        assert cached_response.po_token == EXAMPLE_PO_TOKEN
        assert cached_response.expires_at is not None

        assert len(logger.messages.get('error', [])) == 0